"use client";

import { useEffect, useState } from "react";

function timeRemaining(endDate: string) {
    const diff = new Date(endDate).getTime() - Date.now();
    if (diff <= 0) return "Ended";
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hrs = Math.floor((diff / (1000 * 60 * 60)) % 24);
    return `${days}d ${hrs}h`;
}

export default function RoundTimer({ endDate }: { endDate: string }) {
    const [timeLeft, setTimeLeft] = useState("...");

    useEffect(() => {
        setTimeLeft(timeRemaining(endDate));
        const interval = setInterval(() => {
            setTimeLeft(timeRemaining(endDate));
        }, 1000 * 60); // Update every minute to avoid heavy consistent re-renders for just days/hours
        return () => clearInterval(interval);
    }, [endDate]);

    return <span>{timeLeft}</span>;
}
