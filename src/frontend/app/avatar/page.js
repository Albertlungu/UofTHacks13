"use client";

import dynamic from "next/dynamic";

import { Button } from "../../components/ui/button";

const AvatarView = dynamic(() => import("../../components/three/App"), {
  ssr: false,
});

export default function AvatarPage() {
  return (
    <div className="min-h-screen bg-background">
      <AvatarView />
      <div className="fixed right-4 top-4 z-50">
        <Button type="button" variant="outline" onClick={() => window.close()}>
          Close tab
        </Button>
      </div>
    </div>
  );
}
