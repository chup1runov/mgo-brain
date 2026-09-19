# Public technical references used in the audit

Checked on 2026-09-19. These are external primary documentation references, not copied manufacturer manuals and not evidence about the actual Microcar wiring.

- Linux kernel SocketCAN documentation: https://docs.kernel.org/networking/can.html — driver/interface configuration, virtual CAN and CAN controller modes. An application without send() does not by itself set a CAN controller into listen-only mode.
- Victron VE.Direct protocol FAQ: https://www.victronenergy.com/live/vedirect_protocol:faq — text block framing and the binary checksum byte; the sum of the complete block bytes must be zero modulo 256.
- MDN Service Worker API: https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API — secure-context restrictions. Localhost and an ordinary HTTP LAN hostname are not interchangeable.
- MDN Screen Wake Lock API: https://developer.mozilla.org/en-US/docs/Web/API/Screen_Wake_Lock_API — browser support, permission and secure-context constraints.
- OpenAI Responses API reference: https://platform.openai.com/docs/api-reference/responses/create — request structure, output limits, store parameter; a configured model identifier must be available in the API account.
- OpenAI billing help: https://help.openai.com/en/articles/9039756-billing-settings-in-chatgpt-vs-platform — ChatGPT subscription billing and API platform billing are separate.

The exact dependency versions used by a run are visible in its installation logs. No real external paid AI request was made for these tests; injected test clients validate request shape only.
