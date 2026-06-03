"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function BoardPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/activities");
  }, [router]);

  return null;
}
