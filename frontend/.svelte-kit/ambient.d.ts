
// this file is generated — do not edit it


/// <reference types="@sveltejs/kit" />

/**
 * This module provides access to environment variables that are injected _statically_ into your bundle at build time and are limited to _private_ access.
 * 
 * |         | Runtime                                                                    | Build time                                                               |
 * | ------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
 * | Private | [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private) | [`$env/static/private`](https://svelte.dev/docs/kit/$env-static-private) |
 * | Public  | [`$env/dynamic/public`](https://svelte.dev/docs/kit/$env-dynamic-public)   | [`$env/static/public`](https://svelte.dev/docs/kit/$env-static-public)   |
 * 
 * Static environment variables are [loaded by Vite](https://vitejs.dev/guide/env-and-mode.html#env-files) from `.env` files and `process.env` at build time and then statically injected into your bundle at build time, enabling optimisations like dead code elimination.
 * 
 * **_Private_ access:**
 * 
 * - This module cannot be imported into client-side code
 * - This module only includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://svelte.dev/docs/kit/configuration#env) (if configured)
 * 
 * For example, given the following build time environment:
 * 
 * ```env
 * ENVIRONMENT=production
 * PUBLIC_BASE_URL=http://site.com
 * ```
 * 
 * With the default `publicPrefix` and `privatePrefix`:
 * 
 * ```ts
 * import { ENVIRONMENT, PUBLIC_BASE_URL } from '$env/static/private';
 * 
 * console.log(ENVIRONMENT); // => "production"
 * console.log(PUBLIC_BASE_URL); // => throws error during build
 * ```
 * 
 * The above values will be the same _even if_ different values for `ENVIRONMENT` or `PUBLIC_BASE_URL` are set at runtime, as they are statically replaced in your code with their build time values.
 */
declare module '$env/static/private' {
	export const NODE_ENV: string;
	export const AGY_BROWSER_ACTIVE_PORT_FILE: string;
	export const HOMEBREW_CELLAR: string;
	export const INFOPATH: string;
	export const npm_config_user_agent: string;
	export const ANTIGRAVITY_AGENTAPI_EXE: string;
	export const npm_lifecycle_script: string;
	export const CONDA_PYTHON_EXE: string;
	export const npm_config_cache: string;
	export const CHROME_DEVTOOLS_MCP_JS: string;
	export const ANTIGRAVITY_LS_ADDRESS: string;
	export const ANTIGRAVITY_TRAJECTORY_ID: string;
	export const npm_config_prefix: string;
	export const SHLVL: string;
	export const XPC_SERVICE_NAME: string;
	export const npm_package_version: string;
	export const ZSH_TMUX_AUTOSTARTED: string;
	export const ANTIGRAVITY_CSRF_TOKEN: string;
	export const npm_lifecycle_event: string;
	export const XPC_FLAGS: string;
	export const npm_command: string;
	export const USER: string;
	export const __CFBundleIdentifier: string;
	export const TMPDIR: string;
	export const CONDA_PREFIX: string;
	export const _P9K_SSH_TTY: string;
	export const __CF_USER_TEXT_ENCODING: string;
	export const npm_config_init_module: string;
	export const npm_config_npm_version: string;
	export const DISABLE_AUTO_UPDATE: string;
	export const npm_execpath: string;
	export const npm_config_userconfig: string;
	export const npm_config_engine_strict: string;
	export const ANTIGRAVITY_CONVERSATION_ID: string;
	export const PATH: string;
	export const SVELTEKIT_FORK: string;
	export const npm_node_execpath: string;
	export const _: string;
	export const OSLogRateLimit: string;
	export const _CE_CONDA: string;
	export const ANTIGRAVITY_PROJECT_ID: string;
	export const npm_package_json: string;
	export const AGY_BROWSER_WS_URL: string;
	export const COLOR: string;
	export const ANTIGRAVITY_LS_VERSION: string;
	export const _CE_M: string;
	export const npm_config_node_gyp: string;
	export const NVM_CD_FLAGS: string;
	export const PWD: string;
	export const HOME: string;
	export const NVM_INC: string;
	export const FPATH: string;
	export const P9K_SSH: string;
	export const SSH_AUTH_SOCK: string;
	export const CONDA_EXE: string;
	export const COMMAND_MODE: string;
	export const NVM_DIR: string;
	export const LOGNAME: string;
	export const npm_config_local_prefix: string;
	export const npm_package_name: string;
	export const npm_config_noproxy: string;
	export const LANG: string;
	export const SHELL: string;
	export const CONDA_PROMPT_MODIFIER: string;
	export const npm_config_global_prefix: string;
	export const NODE: string;
	export const INIT_CWD: string;
	export const CONDA_SHLVL: string;
	export const ANTIGRAVITY_SOURCE_METADATA: string;
	export const CONDA_DEFAULT_ENV: string;
	export const npm_config_globalconfig: string;
	export const NVM_BIN: string;
	export const HOMEBREW_PREFIX: string;
	export const HOMEBREW_REPOSITORY: string;
	export const EDITOR: string;
	export const ZSH_TMUX_AUTOSTART: string;
	export const ANTIGRAVITY_AGENT: string;
}

/**
 * This module provides access to environment variables that are injected _statically_ into your bundle at build time and are _publicly_ accessible.
 * 
 * |         | Runtime                                                                    | Build time                                                               |
 * | ------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
 * | Private | [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private) | [`$env/static/private`](https://svelte.dev/docs/kit/$env-static-private) |
 * | Public  | [`$env/dynamic/public`](https://svelte.dev/docs/kit/$env-dynamic-public)   | [`$env/static/public`](https://svelte.dev/docs/kit/$env-static-public)   |
 * 
 * Static environment variables are [loaded by Vite](https://vitejs.dev/guide/env-and-mode.html#env-files) from `.env` files and `process.env` at build time and then statically injected into your bundle at build time, enabling optimisations like dead code elimination.
 * 
 * **_Public_ access:**
 * 
 * - This module _can_ be imported into client-side code
 * - **Only** variables that begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) (which defaults to `PUBLIC_`) are included
 * 
 * For example, given the following build time environment:
 * 
 * ```env
 * ENVIRONMENT=production
 * PUBLIC_BASE_URL=http://site.com
 * ```
 * 
 * With the default `publicPrefix` and `privatePrefix`:
 * 
 * ```ts
 * import { ENVIRONMENT, PUBLIC_BASE_URL } from '$env/static/public';
 * 
 * console.log(ENVIRONMENT); // => throws error during build
 * console.log(PUBLIC_BASE_URL); // => "http://site.com"
 * ```
 * 
 * The above values will be the same _even if_ different values for `ENVIRONMENT` or `PUBLIC_BASE_URL` are set at runtime, as they are statically replaced in your code with their build time values.
 */
declare module '$env/static/public' {
	
}

/**
 * This module provides access to environment variables set _dynamically_ at runtime and that are limited to _private_ access.
 * 
 * |         | Runtime                                                                    | Build time                                                               |
 * | ------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
 * | Private | [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private) | [`$env/static/private`](https://svelte.dev/docs/kit/$env-static-private) |
 * | Public  | [`$env/dynamic/public`](https://svelte.dev/docs/kit/$env-dynamic-public)   | [`$env/static/public`](https://svelte.dev/docs/kit/$env-static-public)   |
 * 
 * Dynamic environment variables are defined by the platform you're running on. For example if you're using [`adapter-node`](https://github.com/sveltejs/kit/tree/main/packages/adapter-node) (or running [`vite preview`](https://svelte.dev/docs/kit/cli)), this is equivalent to `process.env`.
 * 
 * **_Private_ access:**
 * 
 * - This module cannot be imported into client-side code
 * - This module includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://svelte.dev/docs/kit/configuration#env) (if configured)
 * 
 * > [!NOTE] In `dev`, `$env/dynamic` includes environment variables from `.env`. In `prod`, this behavior will depend on your adapter.
 * 
 * > [!NOTE] To get correct types, environment variables referenced in your code should be declared (for example in an `.env` file), even if they don't have a value until the app is deployed:
 * >
 * > ```env
 * > MY_FEATURE_FLAG=
 * > ```
 * >
 * > You can override `.env` values from the command line like so:
 * >
 * > ```sh
 * > MY_FEATURE_FLAG="enabled" npm run dev
 * > ```
 * 
 * For example, given the following runtime environment:
 * 
 * ```env
 * ENVIRONMENT=production
 * PUBLIC_BASE_URL=http://site.com
 * ```
 * 
 * With the default `publicPrefix` and `privatePrefix`:
 * 
 * ```ts
 * import { env } from '$env/dynamic/private';
 * 
 * console.log(env.ENVIRONMENT); // => "production"
 * console.log(env.PUBLIC_BASE_URL); // => undefined
 * ```
 */
declare module '$env/dynamic/private' {
	export const env: {
		NODE_ENV: string;
		AGY_BROWSER_ACTIVE_PORT_FILE: string;
		HOMEBREW_CELLAR: string;
		INFOPATH: string;
		npm_config_user_agent: string;
		ANTIGRAVITY_AGENTAPI_EXE: string;
		npm_lifecycle_script: string;
		CONDA_PYTHON_EXE: string;
		npm_config_cache: string;
		CHROME_DEVTOOLS_MCP_JS: string;
		ANTIGRAVITY_LS_ADDRESS: string;
		ANTIGRAVITY_TRAJECTORY_ID: string;
		npm_config_prefix: string;
		SHLVL: string;
		XPC_SERVICE_NAME: string;
		npm_package_version: string;
		ZSH_TMUX_AUTOSTARTED: string;
		ANTIGRAVITY_CSRF_TOKEN: string;
		npm_lifecycle_event: string;
		XPC_FLAGS: string;
		npm_command: string;
		USER: string;
		__CFBundleIdentifier: string;
		TMPDIR: string;
		CONDA_PREFIX: string;
		_P9K_SSH_TTY: string;
		__CF_USER_TEXT_ENCODING: string;
		npm_config_init_module: string;
		npm_config_npm_version: string;
		DISABLE_AUTO_UPDATE: string;
		npm_execpath: string;
		npm_config_userconfig: string;
		npm_config_engine_strict: string;
		ANTIGRAVITY_CONVERSATION_ID: string;
		PATH: string;
		SVELTEKIT_FORK: string;
		npm_node_execpath: string;
		_: string;
		OSLogRateLimit: string;
		_CE_CONDA: string;
		ANTIGRAVITY_PROJECT_ID: string;
		npm_package_json: string;
		AGY_BROWSER_WS_URL: string;
		COLOR: string;
		ANTIGRAVITY_LS_VERSION: string;
		_CE_M: string;
		npm_config_node_gyp: string;
		NVM_CD_FLAGS: string;
		PWD: string;
		HOME: string;
		NVM_INC: string;
		FPATH: string;
		P9K_SSH: string;
		SSH_AUTH_SOCK: string;
		CONDA_EXE: string;
		COMMAND_MODE: string;
		NVM_DIR: string;
		LOGNAME: string;
		npm_config_local_prefix: string;
		npm_package_name: string;
		npm_config_noproxy: string;
		LANG: string;
		SHELL: string;
		CONDA_PROMPT_MODIFIER: string;
		npm_config_global_prefix: string;
		NODE: string;
		INIT_CWD: string;
		CONDA_SHLVL: string;
		ANTIGRAVITY_SOURCE_METADATA: string;
		CONDA_DEFAULT_ENV: string;
		npm_config_globalconfig: string;
		NVM_BIN: string;
		HOMEBREW_PREFIX: string;
		HOMEBREW_REPOSITORY: string;
		EDITOR: string;
		ZSH_TMUX_AUTOSTART: string;
		ANTIGRAVITY_AGENT: string;
		[key: `PUBLIC_${string}`]: undefined;
		[key: `${string}`]: string | undefined;
	}
}

/**
 * This module provides access to environment variables set _dynamically_ at runtime and that are _publicly_ accessible.
 * 
 * |         | Runtime                                                                    | Build time                                                               |
 * | ------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
 * | Private | [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private) | [`$env/static/private`](https://svelte.dev/docs/kit/$env-static-private) |
 * | Public  | [`$env/dynamic/public`](https://svelte.dev/docs/kit/$env-dynamic-public)   | [`$env/static/public`](https://svelte.dev/docs/kit/$env-static-public)   |
 * 
 * Dynamic environment variables are defined by the platform you're running on. For example if you're using [`adapter-node`](https://github.com/sveltejs/kit/tree/main/packages/adapter-node) (or running [`vite preview`](https://svelte.dev/docs/kit/cli)), this is equivalent to `process.env`.
 * 
 * **_Public_ access:**
 * 
 * - This module _can_ be imported into client-side code
 * - **Only** variables that begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) (which defaults to `PUBLIC_`) are included
 * 
 * > [!NOTE] In `dev`, `$env/dynamic` includes environment variables from `.env`. In `prod`, this behavior will depend on your adapter.
 * 
 * > [!NOTE] To get correct types, environment variables referenced in your code should be declared (for example in an `.env` file), even if they don't have a value until the app is deployed:
 * >
 * > ```env
 * > MY_FEATURE_FLAG=
 * > ```
 * >
 * > You can override `.env` values from the command line like so:
 * >
 * > ```sh
 * > MY_FEATURE_FLAG="enabled" npm run dev
 * > ```
 * 
 * For example, given the following runtime environment:
 * 
 * ```env
 * ENVIRONMENT=production
 * PUBLIC_BASE_URL=http://example.com
 * ```
 * 
 * With the default `publicPrefix` and `privatePrefix`:
 * 
 * ```ts
 * import { env } from '$env/dynamic/public';
 * console.log(env.ENVIRONMENT); // => undefined, not public
 * console.log(env.PUBLIC_BASE_URL); // => "http://example.com"
 * ```
 * 
 * ```
 * 
 * ```
 */
declare module '$env/dynamic/public' {
	export const env: {
		[key: `PUBLIC_${string}`]: string | undefined;
	}
}
