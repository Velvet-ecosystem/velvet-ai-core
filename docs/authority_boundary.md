# Core decisions and Runtime execution

`Court.evaluate(intent, context)` remains a pure descriptive/educational decision
API. Its Receipt, including `authorized=True`, is not an authenticated execution
capability and cannot prove expiry, replay status or parameter binding.

Core's exported `Dispatcher` is retired. Both `register` and `dispatch` always
raise `ConsequentialDispatchRetiredError` (a `RuntimeError`) before consulting
an approval object, registry or handler. Imports remain available to give legacy
callers an explicit migration failure. There is no `simulation_only` switch:
arbitrary callbacks could perform real I/O regardless of that label.

For educational evaluation, keep using `Court.evaluate` and inspect its decision
without invoking a handler. Existing Ghost CAN proposal evaluation remains
available. Do not route real device work through `IntentHandler` or a direct
callback. Submit consequential intent through Velvet Runtime's existing gateway,
Court, signed capability verification, safety gate, persistent replay consumption,
start receipt and approved executor; observe the resulting execution evidence.

This intentionally breaks old callback execution rather than treating a few field
comparisons as sufficient authorization. Core does not import Runtime or implement
a second token/authorization framework. No physical executor is enabled here.
