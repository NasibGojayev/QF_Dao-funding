"use client";

import dynamic from "next/dynamic";

const ThreeScene = dynamic(() => import("./ThreeScene"), {
    ssr: false,
    loading: () => <div className="w-full h-[250px] md:h-[300px] flex items-center justify-center bg-card/10 rounded-xl animate-pulse" />
});

export default function ThreeBackground() {
    return <ThreeScene />;
}
