"use client";

import dynamic from "next/dynamic";

import { Button } from "../../components/ui/button";

const BlockBuilder3D = dynamic(
  () => import("../../components/three/BlockBuilder3D"),
  { ssr: false }
);

export default function ThreePage() {
  return (
    <div className="min-h-screen bg-background">
      <BlockBuilder3D />
      <div className="fixed right-4 top-4 z-50">
        <Button type="button" variant="outline" onClick={() => window.close()}>
          Close tab
        </Button>
      </div>
    </div>
  );
}
