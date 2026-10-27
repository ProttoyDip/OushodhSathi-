import json

import httpx
import pytest

from app import llm_router
from app.agent import ExtractedItem, Extraction, _extract_plain
from app.explain import SAFETY_SENTENCE, explain_flag, is_safe, template
from app.llm_router import NoProviderAvailable, Router
from app.models import MedicineItem, StoredFlag


def _flag(**kw):
    base = dict(id=1, patient_id=1, key="k", code="DUPLICATE_GENERIC", severity="red", item_ids=[1, 2],
                evidence="Napa and Ace both contain paracetamol.", routed_to="doctor", data_source="seed",
                meta={"generic": "paracetamol"}, status="confirmed", created_at="2026-10-26T00:00:00")
    return StoredFlag(**{**base, **kw})


ITEMS = [MedicineItem(id=1, patient_id=1, brand="Napa", generic="paracetamol"),
         MedicineItem(id=2, patient_id=1, brand="Ace", generic="paracetamol")]


@pytest.fixture
def two_providers(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "k1")
    monkeypatch.setenv("OPENROUTER_TEXT_MODEL", "first/model")
    monkeypatch.setenv("OPENROUTER_VISION_MODEL", "first/vision")
    monkeypatch.setenv("NARAROUTER_BASE_URL", "https://second.example/v1")
    monkeypatch.setenv("NARAROUTER_API_KEY", "k2")
    monkeypatch.setenv("NARAROUTER_MODEL", "second/model")


def _reply(text):
    return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


def _router(handler, store=None):
    return Router(store=store, client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_router_falls_back_when_first_provider_fails(two_providers, store):
    calls = []

    def handler(request: httpx.Request):
        calls.append(request.url.host)
        if request.url.host == "openrouter.ai":
            return httpx.Response(429, json={"error": "rate limited"})
        return _reply("hello from second")

    router = _router(handler, store)
    out = router.chat("text", [{"role": "user", "content": "hi"}])
    assert out.provider == "nararouter" and out.text == "hello from second"
    assert calls == ["openrouter.ai", "second.example"]
    again = router.chat("text", [{"role": "user", "content": "hi"}])
    assert again.cached  # served from the SQLite cache after OpenRouter fails again


def test_router_falls_back_on_timeout_and_raises_when_all_fail(two_providers):
    def handler(request):
        raise httpx.ConnectTimeout("slow")

    with pytest.raises(NoProviderAvailable):
        _router(handler).chat("text", [{"role": "user", "content": "hi"}])


def test_router_without_providers_raises():
    with pytest.raises(NoProviderAvailable):
        _router(lambda r: _reply("x")).chat("text", [{"role": "user", "content": "hi"}])


def test_free_model_autopick_prefers_largest_free_vision_context():
    models = {"data": [
        {"id": "paid/vision", "pricing": {"prompt": "0.001", "completion": "0.002"},
         "architecture": {"input_modalities": ["text", "image"]}, "context_length": 999999},
        {"id": "free/small", "pricing": {"prompt": "0", "completion": "0"},
         "architecture": {"input_modalities": ["text", "image"]}, "context_length": 8000},
        {"id": "free/big", "pricing": {"prompt": "0", "completion": "0"},
         "architecture": {"input_modalities": ["text", "image"]}, "context_length": 128000},
        {"id": "free/textonly", "pricing": {"prompt": "0", "completion": "0"},
         "architecture": {"input_modalities": ["text"]}, "context_length": 1000000},
    ]}
    llm_router._auto_models.clear()
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=models)))
    assert llm_router.pick_free_openrouter_model("vision", client) == "free/big"
    llm_router._auto_models.clear()


def test_autopick_probes_and_skips_models_that_refuse():
    models = {"data": [
        {"id": f"free/m{i}", "pricing": {"prompt": "0", "completion": "0"},
         "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]}, "context_length": 1000 - i}
        for i in range(5)
    ] + [{"id": "free/music", "pricing": {"prompt": "0", "completion": "0"},
          "architecture": {"input_modalities": ["text"], "output_modalities": ["audio"]}, "context_length": 99999}]}

    def handler(request: httpx.Request):
        if request.method == "GET":
            return httpx.Response(200, json=models)
        model = json.loads(request.content)["model"]
        return httpx.Response(403 if model == "free/m0" else 200, json={"choices": [{"message": {"content": "o"}}]})

    llm_router._auto_models.clear()
    picked = llm_router.pick_free_openrouter_models("text", "k", httpx.Client(transport=httpx.MockTransport(handler)))
    assert picked == ["free/m1", "free/m2", "free/m3", llm_router.OPENROUTER_FALLBACK]  # m0 refused, music skipped
    llm_router._auto_models.clear()


def test_chosen_model_goes_first_and_the_rest_stay_as_fallback(two_providers):
    before = [(p.name, p.model) for p in llm_router.configured_providers("text")]
    assert before == [("openrouter", "first/model"), ("nararouter", "second/model")]
    llm_router.set_preferred("text", "nararouter", "second/model")
    after = [(p.name, p.model) for p in llm_router.configured_providers("text")]
    assert after == [("nararouter", "second/model"), ("openrouter", "first/model")]
    llm_router.set_preferred("text", None, None)


def test_model_preference_api(two_providers, client):
    tasks = client.get("/models").json()["tasks"]
    assert tasks["text"]["chain"][0] == {"provider": "openrouter", "model": "first/model"}
    assert "k1" not in json.dumps(tasks)  # names only, never keys
    r = client.put("/models/preference", json={"kind": "text", "provider": "nararouter", "model": "second/model"})
    assert r.status_code == 200 and r.json()["tasks"]["text"]["chain"][0]["provider"] == "nararouter"
    bad = client.put("/models/preference", json={"kind": "text", "provider": "openrouter", "model": "not/real"})
    assert bad.status_code == 422
    reset = client.put("/models/preference", json={"kind": "text"}).json()
    assert reset["tasks"]["text"]["preferred"] is None


@pytest.mark.parametrize("bad", [
    "নাপা ৫০০ mg করে খাবেন।",
    "Take 2 টি daily",
    "এখনই ওষুধটি বন্ধ করুন।",
    "এস খাওয়া বাদ দিন।",
    "দিনে ৩ বার খাবেন",
])
def test_explanation_guard_blocks_dosing_and_stop_text(bad):
    assert not is_safe(bad)


def test_explanation_falls_back_to_template_when_llm_gives_dosing(two_providers):
    router = _router(lambda r: _reply("নাপা ও এস দুটোই প্যারাসিটামল। এখন থেকে দিনে ২ টি খাবেন।"))
    text, how = explain_flag(_flag(), ITEMS, "seen", router)
    assert how == "template" and text == template(_flag(), ITEMS)
    assert text.endswith(SAFETY_SENTENCE) and is_safe(text)


def test_explanation_appends_safety_sentence(two_providers):
    router = _router(lambda r: _reply("নাপা ও এস দুটোই প্যারাসিটামল। ডাক্তার বিষয়টি দেখেছেন।"))
    text, how = explain_flag(_flag(), ITEMS, "seen", router)
    assert how.startswith("llm:") and text.endswith(SAFETY_SENTENCE)


def test_explanations_only_for_confirmed_flags():
    with pytest.raises(ValueError):
        explain_flag(_flag(status="pending_review"), ITEMS, None, None)


def test_every_template_is_safe():
    for code, meta in [("DUPLICATE_GENERIC", {"generic": "paracetamol"}), ("THERAPEUTIC_DUPLICATION", {}),
                       ("INTERACTION", {"effect_bn": "ঝুঁকি"}), ("BEERS_65", {"reason_bn": "ঝুঁকি"}),
                       ("EXPIRED", {})]:
        t = template(_flag(code=code, meta=meta), ITEMS)
        assert is_safe(t) and t.endswith(SAFETY_SENTENCE)


def test_explanation_redacts_patient_name(two_providers):
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return _reply("ঠিক আছে।")

    explain_flag(_flag(), ITEMS, "Rahima Begum should bring both strips", _router(handler),
                 redact=["Rahima Begum"])
    assert seen and "Rahima" not in json.dumps(seen, ensure_ascii=False)


def test_agent_output_validation_rejects_bad_json():
    with pytest.raises(Exception):
        Extraction.model_validate({"items": [{"brand": "", "confidence": 2}]})
    with pytest.raises(Exception):
        ExtractedItem.model_validate({"brand": "Napa"})  # confidence is required
    ok = ExtractedItem.model_validate({"brand": "Napa", "confidence": 0.9, "expiry": "2027-3", "prescriber": "null"})
    assert ok.expiry == "2027-03" and ok.prescriber is None


def test_plain_extraction_retries_once_then_marks_needs_review(two_providers):
    replies = iter(["not json at all", '{"items": [{"brand": "Napa", "confidence": "high"}]}'])
    items, _provider, _model, needs_review = _extract_plain(_router(lambda r: _reply(next(replies))),
                                                            b"img", "image/jpeg")
    assert needs_review
    assert [i.brand for i in items] == ["Napa"] and items[0].confidence < 0.75


def test_plain_extraction_accepts_fenced_json(two_providers):
    text = ('```json\n{"items":[{"brand":"Seclo","strength":"20 mg","form":"capsule","expiry":"2027-01",'
            '"source":"strip","prescriber":null,"confidence":0.92}]}\n```')
    items, _p, _m, needs_review = _extract_plain(_router(lambda r: _reply(text)), b"img", "image/jpeg")
    assert not needs_review and items[0].brand == "Seclo" and items[0].expiry == "2027-01"


def test_shelf_agent_runs_with_tools_and_typed_output():
    from pydantic_ai.models.test import TestModel

    from app.agent import ShelfDeps, build_agent
    model = TestModel(call_tools=["match_brand", "check_medicines"])
    result = build_agent(model).run_sync("Read every medicine in this photo.", deps=ShelfDeps(age=68))
    assert isinstance(result.output, Extraction)
    tool_names = {t.name for t in model.last_model_request_parameters.function_tools}
    assert {"match_brand", "lookup_unknown_brand", "check_medicines"} <= tool_names


def test_perplexity_agent_response_parsing():
    from app.research import _perplexity_answer
    data = {"output": [
        {"type": "search_results", "results": [{"id": 1, "url": "https://medex.com.bd/a"}, {"id": 2, "url": "https://arogga.com/b"}]},
        {"type": "message", "content": [{"type": "output_text", "text": '{"generic":"omeprazole","source_index":2}'}]},
    ]}
    text, urls = _perplexity_answer(data)
    assert json.loads(text)["source_index"] == 2 and urls == ["https://medex.com.bd/a", "https://arogga.com/b"]



def test_bangla_quality_guard():
    from app.explain import is_good_bangla
    good = "নাপা ও এস — নাম আলাদা হলেও দুটোই আসলে একই ওষুধ: প্যারাসিটামল। ডাক্তার বিষয়টি দেখেছেন।"
    assert is_good_bangla(good)
    assert not is_good_bangla("নাপা এবং আেস দুটির মধ্যে একই উপাদান আছে।")  # sign on a standalone vowel (real model output)
    assert not is_good_bangla("Napa and Ace both contain paracetamol. The doctor reviewed it.")  # not Bangla
    assert is_good_bangla("Napa ও Ace দুটোই প্যারাসিটামল; ডাক্তার বিষয়টি দেখেছেন।")  # Latin brand names are fine
    assert is_good_bangla("কোৗ")  # two-part ৌ folds correctly


def test_every_template_is_good_bangla():
    from app.explain import is_good_bangla
    for code, meta in [("DUPLICATE_GENERIC", {"generic": "paracetamol"}), ("THERAPEUTIC_DUPLICATION", {}),
                       ("INTERACTION", {"effect_bn": "ঝুঁকি বাড়তে পারে।"}), ("BEERS_65", {"reason_bn": "ঝুঁকি বেশি।"}),
                       ("EXPIRED", {})]:
        assert is_good_bangla(template(_flag(code=code, meta=meta), ITEMS)), code


def test_malformed_llm_bangla_falls_back_to_template(two_providers):
    router = _router(lambda r: _reply("নাপা এবং আেস দুটির মধ্যে একই উপাদান প্যারাসিটামোল আছে।"))
    text, how = explain_flag(_flag(), ITEMS, "seen", router)
    assert how == "template" and text == template(_flag(), ITEMS)



def test_text_only_router_stays_out_of_photo_reading(two_providers, monkeypatch):
    monkeypatch.setenv("NARAROUTER_VISION_MODEL", "none")
    assert [p.name for p in llm_router.configured_providers("vision")] == ["openrouter"]
    assert [p.name for p in llm_router.configured_providers("text")] == ["openrouter", "nararouter"]
    monkeypatch.setenv("NARAROUTER_VISION_MODEL", "seeing/model")
    vision = {p.name: p.model for p in llm_router.configured_providers("vision")}
    assert vision["nararouter"] == "seeing/model"
