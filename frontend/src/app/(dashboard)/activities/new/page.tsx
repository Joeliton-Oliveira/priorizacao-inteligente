"use client";

import { ActivityForm } from "../_components/activity-form/activity-form";
import { ActivityNewPageShell } from "./activity-new-page-shell";

export default function NewActivityPage() {
  return (
    <ActivityNewPageShell>
      <ActivityForm />
    </ActivityNewPageShell>
  );
}
