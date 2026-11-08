# Cleanup after the hackathon

## SSH key `gh-runner-relay-hackathon-0811 (à retirer)` on orbit (added 2026-11-08 ~09:50 UTC by gh-runner2, Martin's explicit OK)

Lets the GitHub runners of `martinbon39/holo-osworld-runner` reach the Feci Guard relay (127.0.0.1:9911) on orbit.
Restricted: `restrict,port-forwarding,permitopen="127.0.0.1:9911",command="/usr/sbin/nologin"`, so no shell and no other port
(both checked locally: shell refused, a forward to port 22 refused, 9911 answered).
Fingerprint: `SHA256:Z2ii0FUhnRx49OO9kLVKoO/4+J4HBCwz+7LezP7F6Kw`. The private key exists only in the GitHub secret.

To remove:

1. On orbit: `sed -i '/gh-runner-relay-hackathon-0811/d' ~/.ssh/authorized_keys`
2. `gh secret delete ORBIT_TUNNEL_KEY -R martinbon39/holo-osworld-runner`
   and `gh secret delete ORBIT_TUNNEL_HOST -R martinbon39/holo-osworld-runner`

Other secrets of that repo to drop when it is no longer used: `MODAL_KEY`, `POD_SSH_KEY`, `POD_SSH_HOST`, `POD_SSH_PORT`.
