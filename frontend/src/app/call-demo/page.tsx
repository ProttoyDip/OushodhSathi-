import { redirect } from "next/navigation";

/** /call-demo: the check-in call simulator on the invented demo household. */
export default function CallDemo() {
  redirect("/p/1/call");
}
