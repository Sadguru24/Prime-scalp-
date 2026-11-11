# Prime Scalp source ZIP — staging manifest

The supplied source ZIP contains 48 root Python modules. 46 pass Python AST parsing; two are quarantined for syntax errors.

## Candidate modules reviewed
- brokers.py
- config.py (existing branch file: compare, do not overwrite blindly)
- core.py
- engine.py
- main.py
- main_indicators.py
- momentum_indicators.py
- scaling.py
- server.py
- strategy_accum_dist.py
- strategy_aroon_starter.py
- strategy_awesome_oscillator.py
- strategy_bharat_index_setup.py
- strategy_bharat_shield.py
- strategy_breakout_volatility_squeeze.py
- strategy_cci_deviation.py
- strategy_chaikin_volatility.py
- strategy_delta_quant_alpha.py
- strategy_donchian_breakout.py
- strategy_ease_of_movement.py
- strategy_force_index.py
- strategy_historical_volatility.py
- strategy_ichimoku_cloud.py
- strategy_kama_hurst.py
- strategy_keltner_channel_scalp.py
- strategy_klinger_oscillator.py
- strategy_mfi_flow.py
- strategy_microstructure.py
- strategy_parabolic_sar.py
- strategy_rate_of_change.py
- strategy_regime.py (existing branch implementation; preserve after diff)
- strategy_registry.py (blocked by package import and quarantined dependencies)
- strategy_rsi_divergence_scalp.py
- strategy_smc.py
- strategy_super_trend_rsi_filter.py
- strategy_ulcer_risk_managed.py
- strategy_volume_profile_poc.py
- strategy_volume_rsi.py
- strategy_vortex_reversal.py
- strategy_vwap_momentum_pullback.py
- strategy_williams_r_scalp.py
- trend_indicators.py
- utils_risk_engine.py
- vault.py
- volatility_indicators.py
- volume_indicators.py

Additional root files: Dockerfile, docker-compose.yml, requirements.txt.

## Existing Integration Branch files requiring comparison
config.py, strategy_regime.py, .github/workflows/quality.yml, README.md, indicators_engine.py, prime_scalp_strategy_suite.py, and existing tests.

## Quarantined syntax failures
- strategy_options_hedge.py — malformed f-string at line 41.
- strategy_swing_brahmastra.py — malformed f-string at line 45.

Generated cache/bytecode/runtime logs are excluded. This is an intake inventory only; no listed module is certified production-ready.
