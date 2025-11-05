# Changelog Draft - ESPHome 2025.11.0 Compatibility

## Upcoming Changes (To be released after testing with ESPHome 2025.11.0-DEV)

### Memory Optimizations
- [ ] Tested LED effects with ESPHome 2025.11.0-DEV memory improvements
- [ ] Evaluated feasibility of re-enabling effects on side lights
- [ ] Updated memory optimization documentation with new findings
- [ ] Performance benchmarks with various feature combinations

### LED Effects Status
Current status: LED effects are enabled for main lights (light_eu/light_us) but disabled for side lights due to memory constraints.

Testing plan:
1. Test current configuration with ESPHome 2025.11.0-DEV
2. Monitor memory usage during boot and operation
3. Evaluate if memory improvements allow for:
   - Effects on side lights
   - More effects on main lights
   - Better coexistence with BLE proxy + media player
4. Document findings and update recommendations

### Notes
- If memory improvements are sufficient, consider creating an optional "full effects" package
- Maintain backward compatibility with existing configurations
- Provide clear migration guide for users upgrading from older versions
- Keep advanced configuration option for users with memory constraints

---
**Testing Checklist:**
- [ ] Core + Relays + LED Effects (all)
- [ ] Core + Relays + LED Effects + BLE Proxy
- [ ] Core + Relays + LED Effects + Media Player
- [ ] Core + Relays + LED Effects + BLE Proxy + Media Player
- [ ] Memory usage logs collected for each configuration
- [ ] Stability testing (24h+ runtime)
- [ ] OTA update success rate with various configurations

**Test Results:** (To be filled during weekend testing)

Configuration tested:
- ESPHome version: 
- Framework: 
- Features enabled: 
- Free heap at boot: 
- Stability issues: None / List issues
- Notes: 