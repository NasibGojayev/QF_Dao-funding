"use client";

import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { logger } from "../lib/logger";

/**
 * LoggingProvider - Wraps the app to provide automatic page navigation logging
 * Use this component in your layout to log all page loads and navigations.
 */
export function LoggingProvider({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const searchParams = useSearchParams();

    useEffect(() => {
        // Log page load/navigation
        const fullPath = searchParams?.toString()
            ? `${pathname}?${searchParams.toString()}`
            : pathname;

        logger.page.load(fullPath);

        // Log initial app load
        if (typeof window !== "undefined") {
            logger.info("APP", `DonCoin DAO loaded at ${new Date().toISOString()}`);
        }
    }, [pathname, searchParams]);

    return <>{children}</>;
}

export default LoggingProvider;
