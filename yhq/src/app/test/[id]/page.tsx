import type { Metadata } from "next";
import { TestRunner } from "@/components/test/test-runner";

export const metadata: Metadata = { title: "Test", robots: { index: false } };

export default async function TestPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <TestRunner attemptId={id} />;
}
