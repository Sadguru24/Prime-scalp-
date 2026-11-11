# Source ZIP staging manifest

This manifest records the initial intake review of the supplied Prime-Scalp-Hub ZIP.

## Candidate source inventory
The review bundle contains 46 syntax-parseable root Python modules plus the root deployment/configuration files. The two broken strategy files are kept out of the executable candidate set.

Candidate root Python modules:
- brokers.py
- config.py (do not overwrite the existing Integration Branch config.py without a deliberate compatibility review)
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

Additional root files in the candidate review bundle:
- Dockerfile
- docker-compose.yml
- requirements.txt

## Existing Integration Branch files that need comparison, not blind overwrite
- config.py
- strategy_regime.py
- .github/workflows/quality.yml
- README.md
- indicators_engine.py
- prime_scalp_strategy_suite.py
- existing tests under tests/

## Quarantined
- strategy_options_hedge.py — syntax error at line 41.
- strategy_swing_brahmastra.py — syntax error at line 45.

## Not staged as executable source
- .pytest_cache/, __pycache__/, *.pyc, runtime logs.
- No generated cache or bytecode should be committed.

## Important
This manifest is an intake record, not a claim that all listed modules have been committed or certified. Initial import/functional/security review remains incomplete. Do not deploy based on this manifest.
