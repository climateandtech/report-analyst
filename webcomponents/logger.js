/**
 * Minimal, dependency-free browser logger.
 *
 * Provides namespaced, level-filtered logging on top of the browser's
 * console API. Levels are ordered so that a logger configured with a given
 * level emits its own level and everything stricter:
 *
 *   debug < info < warn < error
 *
 * Example:
 *   import { Logger } from "./logger.js";
 *   const log = new Logger("benchmark-example");
 *   log.info("Component connected.");
 */

export const LOG_LEVELS = Object.freeze({
	debug: 10,
	info: 20,
	warn: 30,
	error: 40,
});

const DEFAULT_LEVEL = "info";

// Maps our log levels to the corresponding console method.
const CONSOLE_METHODS = Object.freeze({
	debug: "debug",
	info: "log",
	warn: "warn",
	error: "error",
});

export class Logger {
	#namespace;
	#level = LOG_LEVELS[DEFAULT_LEVEL];

	constructor(namespace, level = DEFAULT_LEVEL) {
		if (typeof namespace !== "string" || namespace.length === 0) {
			throw new TypeError("Logger namespace must be a non-empty string.");
		}
		this.#namespace = namespace;
		this.setLevel(level);
	}

	get namespace() {
		return this.#namespace;
	}

	get level() {
		return this.#level;
	}

	setLevel(level) {
		if (Object.prototype.hasOwnProperty.call(LOG_LEVELS, level)) {
			this.#level = LOG_LEVELS[level];
		}
		return this;
	}

	#enabled(level) {
		return this.#level <= LOG_LEVELS[level];
	}

	#write(level, args) {
		if (!this.#enabled(level)) {
			return;
		}
		const method = CONSOLE_METHODS[level];
		// eslint-disable-next-line no-console
		console[method](`[${this.#namespace}]`, ...args);
	}

	debug(...args) {
		this.#write("debug", args);
	}

	info(...args) {
		this.#write("info", args);
	}

	warn(...args) {
		this.#write("warn", args);
	}

	error(...args) {
		this.#write("error", args);
	}
}