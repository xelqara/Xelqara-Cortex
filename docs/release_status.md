# BidCore Release Status

## Verified

- 23 local automated tests pass.
- The synthetic 100-trial benchmark runs successfully.
- GitHub Actions passes on Python 3.11 and 3.12 for the published commits.
- The end-to-end enterprise flow from XLSX intake to JSON audit export passes locally.
- The local Flask interface is bound to loopback by default.
- The local model adapter rejects non-loopback Ollama endpoints and structured JSON validation rejects invalid objects.

## Environment note

The sandbox used for development does not contain the Docker executable, so the Dockerfile was syntax-reviewed and committed but not built here. The customer deployment host must run a controlled Docker build or install the package directly, then perform its own security and restore tests.

## Not claimed

No production accuracy, certification, legal approval, autonomous submission, or universal superiority claim is made. Those require a customer-authorized dataset, a defined evaluation protocol, and a security review in the deployment environment.
