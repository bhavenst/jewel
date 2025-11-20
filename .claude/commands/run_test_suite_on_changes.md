# Gateway Changes Validation Command

## 🤖 Claude Prompt for ATF Test Validation

When you make changes to the aap-gateway project and need to validate them using the ATF test-suite, use this prompt with Claude:

```
I modified the aap-gateway project at `aap-gateway`.

I need you to find the test-suite at https://gitlab.cee.redhat.com/ansible/testing/platform-services-test-suite and https://gitlab.cee.redhat.com/ansible/testing/test-suite/-/tree/main/tests/gateway?ref_type=heads to identify all tests that can validate my changes and assure they do not break any existing gateway functionality.

Please provide:
1. Specific test commands to run
2. Test categories relevant to gateway changes
3. Critical tests that should never be skipped
4. A prioritized testing approach (quick smoke tests vs comprehensive validation)

Focus on tests in the test-suite project that validate gateway APIs, authentication, routing, proxy functionality, and model serialization.
```

## 📋 Expected Output

Claude will provide:
- Targeted test commands for your specific changes
- Test execution priorities (quick → standard → comprehensive)
- Critical validation tests that must pass
- Specific pytest commands for the ATF test-suite

## 📍 Key Locations
- **Gateway Project**: `aap-gateway`
- **Test Suite**: `https://gitlab.cee.redhat.com/ansible/testing/platform-services-test-suite`
- **Gateway Tests**: `https://gitlab.cee.redhat.com/ansible/testing/test-suite/-/tree/main/tests/gateway`
