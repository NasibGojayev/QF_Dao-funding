/**
 * Frontend Logger Utility
 * Provides structured logging for Next.js client-side operations.
 * Logs to console and stores in localStorage with rotation.
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
    timestamp: string;
    level: LogLevel;
    category: string;
    message: string;
    data?: any;
}

const MAX_LOCAL_LOGS = 500;
const STORAGE_KEY = 'doncoin_logs';

class Logger {
    private isDev: boolean;

    constructor() {
        this.isDev = process.env.NODE_ENV === 'development';
    }

    private formatMessage(level: LogLevel, category: string, message: string): string {
        const timestamp = new Date().toISOString();
        return `[${timestamp}] [${level.toUpperCase()}] [${category}] ${message}`;
    }

    private storeLog(entry: LogEntry): void {
        if (typeof window === 'undefined') return;

        try {
            const logs: LogEntry[] = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
            logs.push(entry);

            // Rotate logs if exceeding max
            if (logs.length > MAX_LOCAL_LOGS) {
                logs.splice(0, logs.length - MAX_LOCAL_LOGS);
            }

            localStorage.setItem(STORAGE_KEY, JSON.stringify(logs));
        } catch (e) {
            // localStorage might be full or unavailable
            console.warn('Failed to store log:', e);
        }
    }

    private log(level: LogLevel, category: string, message: string, data?: any): void {
        const timestamp = new Date().toISOString();
        const formattedMsg = this.formatMessage(level, category, message);

        // Console output (always in dev, only errors in prod)
        if (this.isDev || level === 'error') {
            const consoleMethod = level === 'error' ? console.error :
                level === 'warn' ? console.warn :
                    level === 'debug' ? console.debug : console.log;

            if (data) {
                consoleMethod(formattedMsg, data);
            } else {
                consoleMethod(formattedMsg);
            }
        }

        // Store in localStorage
        this.storeLog({
            timestamp,
            level,
            category,
            message,
            data: data ? JSON.parse(JSON.stringify(data)) : undefined,
        });
    }

    // Public logging methods
    debug(category: string, message: string, data?: any): void {
        this.log('debug', category, message, data);
    }

    info(category: string, message: string, data?: any): void {
        this.log('info', category, message, data);
    }

    warn(category: string, message: string, data?: any): void {
        this.log('warn', category, message, data);
    }

    error(category: string, message: string, data?: any): void {
        this.log('error', category, message, data);
    }

    // Specialized loggers
    api = {
        request: (method: string, url: string, body?: any) => {
            this.info('API', `→ ${method} ${url}`, body ? { body } : undefined);
        },

        response: (method: string, url: string, status: number, duration: number, data?: any) => {
            const level = status >= 400 ? 'error' : 'info';
            this.log(level, 'API', `← ${status} ${method} ${url} (${duration}ms)`, data);
        },

        error: (method: string, url: string, error: any) => {
            this.error('API', `✕ ${method} ${url} failed`, { error: String(error) });
        }
    };

    page = {
        load: (path: string) => {
            this.info('PAGE', `Loaded: ${path}`);
        },

        navigate: (from: string, to: string) => {
            this.info('PAGE', `Navigate: ${from} → ${to}`);
        }
    };

    blockchain = {
        connect: (provider: string) => {
            this.info('BLOCKCHAIN', `Connecting to ${provider}`);
        },

        contractCall: (contract: string, method: string, args?: any) => {
            this.info('BLOCKCHAIN', `Contract call: ${contract}.${method}`, args);
        },

        transaction: (txHash: string, status: 'pending' | 'confirmed' | 'failed') => {
            const level = status === 'failed' ? 'error' : 'info';
            this.log(level, 'BLOCKCHAIN', `TX ${txHash.substring(0, 16)}...: ${status}`);
        },

        event: (contract: string, eventName: string, data: any) => {
            this.debug('BLOCKCHAIN', `Event: ${contract}.${eventName}`, data);
        }
    };

    wallet = {
        connect: (address: string) => {
            this.info('WALLET', `Connected: ${address.substring(0, 10)}...`);
        },

        disconnect: () => {
            this.info('WALLET', 'Disconnected');
        },

        signMessage: (address: string) => {
            this.info('WALLET', `Signing message for ${address.substring(0, 10)}...`);
        }
    };

    // Utility methods
    getLogs(): LogEntry[] {
        if (typeof window === 'undefined') return [];
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        } catch {
            return [];
        }
    }

    clearLogs(): void {
        if (typeof window === 'undefined') return;
        localStorage.removeItem(STORAGE_KEY);
        this.info('LOGGER', 'Logs cleared');
    }

    exportLogs(): string {
        return JSON.stringify(this.getLogs(), null, 2);
    }
}

// Singleton instance
export const logger = new Logger();

// Default export for convenience
export default logger;
