---- MODULE HomelabDeploy ----
\* One real or dry-run invocation of scripts/homelab-deploy for one enabled
\* service that already has a compose file. The actions follow the script in
\* order. Situations are the inputs the script reads. TLC explores every
\* situation in Situations. It does not explore inputs outside that set.
\*
\* Covered code, as of 5f75448767b00ce529b4d21d85a7d1e445f3c179:
\*   git_branch, git_dirty_state, require_host_identity, require_deploy_allowed,
\*   run_config_validation, prepare_service's return into deploy_service,
\*   joe_owned_compose_services, and deploy_service from the .render-env-skipped
\*   check through write_deploy_state.
\*
\* The promise each invariant names is the one in the script's guard text and
\* in docs/deployment-source-of-truth.md. ConfigProof is the documented rule
\* that only --skip-config-validate skips strict config validation. The script
\* also continues when the validator is missing or not executable. That
\* path is in this model. Do not drop it, and do not weaken ConfigProof.

\* ---------------------------------------------------------------------------
\* Inputs. clean is a real deploy of a Joe-owned image on nasfeo from a clean
\* main checkout, with validation passing and compose succeeding.

clean == [
  dryRun |-> FALSE,
  dirty |-> FALSE,
  allowDirty |-> FALSE,
  host |-> "nasfeo",
  onProductionHost |-> TRUE,
  allowForeignHost |-> FALSE,
  namedBranch |-> "main",
  githubRefName |-> "",
  canary |-> FALSE,
  skipConfigValidate |-> FALSE,
  validator |-> "pass",
  secretsSkipped |-> FALSE,
  prepare |-> "ok",
  service |-> "demo",
  imageOwner |-> "joe",
  pullResult |-> "ok",
  composeResult |-> "ok",
  caddyReload |-> "na"
]

\* Passing deploys.
dirtyAllowMain == [clean EXCEPT !.dirty = TRUE, !.allowDirty = TRUE]
featureCanary == [clean EXCEPT !.namedBranch = "feature", !.canary = TRUE]
macminiOnProd == [clean EXCEPT !.host = "macmini"]
macminiForeign == [clean EXCEPT !.host = "macmini", !.onProductionHost = FALSE, !.allowForeignHost = TRUE]
nasfeoOffMachine == [clean EXCEPT !.onProductionHost = FALSE]
skipDespiteFail == [clean EXCEPT !.skipConfigValidate = TRUE, !.validator = "fail"]
validatorAbsent == [clean EXCEPT !.validator = "absent"]
thirdParty == [clean EXCEPT !.imageOwner = "third"]
transientPull == [clean EXCEPT !.pullResult = "transient"]
caddyHappy == [clean EXCEPT !.service = "caddy", !.caddyReload = "ok"]
namedMainPrRef == [clean EXCEPT !.githubRefName = "50/merge"]
detachedPrRefCanary == [clean EXCEPT !.namedBranch = "detached", !.githubRefName = "50/merge", !.canary = TRUE]

\* Dry-run skips require_deploy_allowed, then still checks secrets.
dryRunSkipsGates == [clean EXCEPT !.dryRun = TRUE, !.dirty = TRUE, !.namedBranch = "feature",
                                !.host = "macmini", !.onProductionHost = FALSE]
dryRunSecrets == [clean EXCEPT !.dryRun = TRUE, !.secretsSkipped = TRUE]

\* Each override skips only its own gate.
dirtyRefuse == [clean EXCEPT !.dirty = TRUE]
dirtyAllowNeedsCanary == [dirtyAllowMain EXCEPT !.namedBranch = "feature"]
dirtyAllowNeedsHost == [dirtyAllowMain EXCEPT !.host = "macmini", !.onProductionHost = FALSE]
dirtyAllowNeedsConfig == [dirtyAllowMain EXCEPT !.validator = "fail"]
canaryDoesNotSkipDirty == [clean EXCEPT !.dirty = TRUE, !.namedBranch = "feature", !.canary = TRUE]
canaryDoesNotSkipHost == [featureCanary EXCEPT !.host = "macmini", !.onProductionHost = FALSE]
canaryDoesNotSkipConfig == [featureCanary EXCEPT !.validator = "fail"]
foreignDoesNotSkipDirty == [clean EXCEPT !.allowForeignHost = TRUE, !.dirty = TRUE,
                                     !.host = "macmini", !.onProductionHost = FALSE]
foreignDoesNotSkipCanary == [macminiForeign EXCEPT !.namedBranch = "feature"]
foreignDoesNotSkipConfig == [macminiForeign EXCEPT !.validator = "fail"]
skipDoesNotSkipDirty == [clean EXCEPT !.skipConfigValidate = TRUE, !.dirty = TRUE]
skipDoesNotSkipCanary == [clean EXCEPT !.skipConfigValidate = TRUE, !.namedBranch = "feature"]
skipDoesNotSkipHost == [clean EXCEPT !.skipConfigValidate = TRUE, !.host = "macmini", !.onProductionHost = FALSE]
hostRefuse == [clean EXCEPT !.host = "macmini", !.onProductionHost = FALSE]
configFail == [clean EXCEPT !.validator = "fail"]
secretsDespiteSkip == [clean EXCEPT !.secretsSkipped = TRUE, !.skipConfigValidate = TRUE]
prepareFail == [caddyHappy EXCEPT !.prepare = "fail"]
pullAuth == [clean EXCEPT !.pullResult = "auth"]
composeFail == [clean EXCEPT !.composeResult = "fail"]
caddyReloadFail == [caddyHappy EXCEPT !.caddyReload = "fail"]
detachedPrRef == [clean EXCEPT !.namedBranch = "detached", !.githubRefName = "50/merge"]
detachedHead == [clean EXCEPT !.namedBranch = "detached"]
featureNamedIgnoresMainRef == [clean EXCEPT !.namedBranch = "feature", !.githubRefName = "main"]

Situations == {
  clean, dirtyAllowMain, featureCanary, macminiOnProd, macminiForeign, nasfeoOffMachine,
  skipDespiteFail, validatorAbsent, thirdParty, transientPull, caddyHappy, namedMainPrRef,
  detachedPrRefCanary, dryRunSkipsGates, dryRunSecrets, dirtyRefuse, dirtyAllowNeedsCanary,
  dirtyAllowNeedsHost, dirtyAllowNeedsConfig, canaryDoesNotSkipDirty, canaryDoesNotSkipHost,
  canaryDoesNotSkipConfig, foreignDoesNotSkipDirty, foreignDoesNotSkipCanary,
  foreignDoesNotSkipConfig, skipDoesNotSkipDirty, skipDoesNotSkipCanary, skipDoesNotSkipHost,
  hostRefuse, configFail, secretsDespiteSkip, prepareFail, pullAuth, composeFail,
  caddyReloadFail, detachedPrRef, detachedHead, featureNamedIgnoresMainRef
}

\* git_branch: a named checkout wins. Detached HEAD uses GITHUB_REF_NAME when
\* that variable is set, and otherwise stays "HEAD", which is not main.
ResolvedBranch(s) ==
  IF s.namedBranch = "detached" /\ s.githubRefName # ""
  THEN s.githubRefName
  ELSE IF s.namedBranch # "detached"
       THEN s.namedBranch
       ELSE "HEAD"

VARIABLES
  situation, pc, refusal, configProof, pull, compose, provenance,
  recordedDirty, recordedCanary

vars == <<situation, pc, refusal, configProof, pull, compose, provenance,
          recordedDirty, recordedCanary>>

TypeOK ==
  /\ situation \in Situations
  /\ pc \in {"start", "dirty", "identity", "canary", "secrets", "config",
             "prepare", "pull", "compose", "reload", "record", "done"}
  /\ refusal \in {"", "dirty", "foreign", "canary", "secrets", "config",
                  "prepare", "pull_auth", "compose", "reload"}
  /\ configProof \in {"unreached", "skipped_dry_run", "skipped_flag",
                      "skipped_absent", "failed", "passed"}
  /\ pull \in {"unreached", "skipped_caddy", "skipped_third_party", "ok",
               "transient", "auth"}
  /\ compose \in {"unreached", "ok", "fail"}
  /\ provenance \in BOOLEAN
  /\ recordedDirty \in BOOLEAN
  /\ recordedCanary \in BOOLEAN

Init ==
  /\ situation \in Situations
  /\ pc = "start"
  /\ refusal = ""
  /\ configProof = "unreached"
  /\ pull = "unreached"
  /\ compose = "unreached"
  /\ provenance = FALSE
  /\ recordedDirty = FALSE
  /\ recordedCanary = FALSE

\* require_deploy_allowed returns immediately for --dry-run. --list is not a
\* deploy and is outside this model. A real deploy enters the dirty gate.
Admit ==
  /\ pc = "start"
  /\ IF situation.dryRun THEN pc' = "secrets" ELSE pc' = "dirty"
  /\ UNCHANGED <<situation, refusal, configProof, pull, compose, provenance,
                 recordedDirty, recordedCanary>>

\* Dirty worktree is the first real-deploy gate. --allow-dirty skips only it.
DirtyGate ==
  /\ pc = "dirty"
  /\ IF situation.dirty /\ ~situation.allowDirty
     THEN /\ pc' = "done"
          /\ refusal' = "dirty"
     ELSE /\ pc' = "identity"
          /\ UNCHANGED refusal
  /\ UNCHANGED <<situation, configProof, pull, compose, provenance,
                 recordedDirty, recordedCanary>>

\* require_host_identity runs only for macmini, and --allow-foreign-host skips
\* only that check. nasfeo returns before deploy_user and bind_addr are read.
\* onProductionHost stands for both halves of the check (deploy_user, then
\* bind_addr). hosts/macmini/services.yaml sets both, so either miss refuses.
IdentityGate ==
  /\ pc = "identity"
  /\ IF situation.host # "macmini" \/ situation.allowForeignHost
     THEN /\ pc' = "canary"
          /\ UNCHANGED refusal
     ELSE IF ~situation.onProductionHost
          THEN /\ pc' = "done"
               /\ refusal' = "foreign"
          ELSE /\ pc' = "canary"
               /\ UNCHANGED refusal
  /\ UNCHANGED <<situation, configProof, pull, compose, provenance,
                 recordedDirty, recordedCanary>>

\* A branch other than main needs --canary. --allow-dirty does not count.
CanaryGate ==
  /\ pc = "canary"
  /\ IF ResolvedBranch(situation) # "main" /\ ~situation.canary
     THEN /\ pc' = "done"
          /\ refusal' = "canary"
     ELSE /\ pc' = "secrets"
          /\ UNCHANGED refusal
  /\ UNCHANGED <<situation, configProof, pull, compose, provenance,
                 recordedDirty, recordedCanary>>

\* .render-env-skipped is checked for dry-runs and real deploys, before
\* config validation. --skip-config-validate does not skip it.
SecretsGate ==
  /\ pc = "secrets"
  /\ IF situation.secretsSkipped
     THEN /\ pc' = "done"
          /\ refusal' = "secrets"
     ELSE /\ pc' = "config"
          /\ UNCHANGED refusal
  /\ UNCHANGED <<situation, configProof, pull, compose, provenance,
                 recordedDirty, recordedCanary>>

\* run_config_validation. Dry-run logs skip. --skip-config-validate logs skip.
\* A missing or non-executable validator logs skip and returns 0. A failing
\* strict check exits 3. A passing check continues.
ConfigGate ==
  /\ pc = "config"
  /\ \/ /\ situation.dryRun
        /\ pc' = "prepare"
        /\ configProof' = "skipped_dry_run"
        /\ UNCHANGED refusal
     \/ /\ ~situation.dryRun
        /\ situation.skipConfigValidate
        /\ pc' = "prepare"
        /\ configProof' = "skipped_flag"
        /\ UNCHANGED refusal
     \/ /\ ~situation.dryRun
        /\ ~situation.skipConfigValidate
        /\ situation.validator = "absent"
        /\ pc' = "prepare"
        /\ configProof' = "skipped_absent"
        /\ UNCHANGED refusal
     \/ /\ ~situation.dryRun
        /\ ~situation.skipConfigValidate
        /\ situation.validator = "fail"
        /\ pc' = "done"
        /\ configProof' = "failed"
        /\ refusal' = "config"
     \/ /\ ~situation.dryRun
        /\ ~situation.skipConfigValidate
        /\ situation.validator = "pass"
        /\ pc' = "prepare"
        /\ configProof' = "passed"
        /\ UNCHANGED refusal
  /\ UNCHANGED <<situation, pull, compose, provenance, recordedDirty, recordedCanary>>

\* deploy_service calls prepare_service. Dry-run returns before the generator.
\* A non-zero return logs prepare fail and exits 1. Only caddy, homepage,
\* homelab-docs, and homelab-functions can return non-zero; prepareFail is
\* the caddy generator failing. Other services return 0.
PrepareStep ==
  /\ pc = "prepare"
  /\ IF situation.dryRun
     THEN /\ pc' = "done"
          /\ UNCHANGED refusal
     ELSE IF situation.prepare = "fail"
          THEN /\ pc' = "done"
               /\ refusal' = "prepare"
          ELSE /\ pc' = "pull"
               /\ UNCHANGED refusal
  /\ UNCHANGED <<situation, configProof, pull, compose, provenance,
                 recordedDirty, recordedCanary>>

\* caddy skips the pull because the workflow built the image locally, even
\* when the compose image is ghcr.io/feocco/*. No Joe-owned service skips the
\* pull. An auth, denied, not-found, or unknown-manifest pull exits 2 inside
\* the subshell. Any other pull failure logs image-pull fail and continues
\* with the cached image. Third-party images are not pulled.
PullStep ==
  /\ pc = "pull"
  /\ \/ /\ situation.service = "caddy"
        /\ pull' = "skipped_caddy"
        /\ pc' = "compose"
        /\ UNCHANGED refusal
     \/ /\ situation.service # "caddy"
        /\ situation.imageOwner = "third"
        /\ pull' = "skipped_third_party"
        /\ pc' = "compose"
        /\ UNCHANGED refusal
     \/ /\ situation.service # "caddy"
        /\ situation.imageOwner = "joe"
        /\ situation.pullResult = "ok"
        /\ pull' = "ok"
        /\ pc' = "compose"
        /\ UNCHANGED refusal
     \/ /\ situation.service # "caddy"
        /\ situation.imageOwner = "joe"
        /\ situation.pullResult = "transient"
        /\ pull' = "transient"
        /\ pc' = "compose"
        /\ UNCHANGED refusal
     \/ /\ situation.service # "caddy"
        /\ situation.imageOwner = "joe"
        /\ situation.pullResult = "auth"
        /\ pull' = "auth"
        /\ pc' = "done"
        /\ refusal' = "pull_auth"
  /\ UNCHANGED <<situation, configProof, compose, provenance, recordedDirty, recordedCanary>>

\* compose up -d --remove-orphans. Failure logs compose-up fail and exits 1
\* inside the subshell, so write_deploy_state does not run. Caddy stays in
\* the subshell for the reload. Other services leave the subshell and record.
ComposeStep ==
  /\ pc = "compose"
  /\ IF situation.composeResult = "fail"
     THEN /\ compose' = "fail"
          /\ pc' = "done"
          /\ refusal' = "compose"
     ELSE /\ compose' = "ok"
          /\ UNCHANGED refusal
          /\ IF situation.service = "caddy" THEN pc' = "reload" ELSE pc' = "record"
  /\ UNCHANGED <<situation, configProof, pull, provenance, recordedDirty, recordedCanary>>

\* caddy reload runs only after compose up succeeds. A failed reload exits 1
\* inside the subshell. Ten retries are one step here: the outcome is the
\* last one. configure-authentik-settings --apply is the same shape and is
\* not a separate situation.
ReloadStep ==
  /\ pc = "reload"
  /\ IF situation.caddyReload = "fail"
     THEN /\ pc' = "done"
          /\ refusal' = "reload"
     ELSE /\ pc' = "record"
          /\ UNCHANGED refusal
  /\ UNCHANGED <<situation, configProof, pull, compose, provenance,
                 recordedDirty, recordedCanary>>

\* write_deploy_state runs only after the subshell returns 0. The JSON records
\* the tree's dirty bit and the --canary flag that was passed.
WriteProvenance ==
  /\ pc = "record"
  /\ pc' = "done"
  /\ provenance' = TRUE
  /\ recordedDirty' = situation.dirty
  /\ recordedCanary' = situation.canary
  /\ UNCHANGED <<situation, refusal, configProof, pull, compose>>

\* End states have no next deploy step. This keeps the run from looking stuck.
Done ==
  /\ pc = "done"
  /\ UNCHANGED vars

Next ==
  \/ Admit
  \/ DirtyGate
  \/ IdentityGate
  \/ CanaryGate
  \/ SecretsGate
  \/ ConfigGate
  \/ PrepareStep
  \/ ComposeStep
  \/ PullStep
  \/ ReloadStep
  \/ WriteProvenance
  \/ Done

Spec == Init /\ [][Next]_vars

\* ---------------------------------------------------------------------------
\* Promises. A failure is a deploy the script should not have finished, or a
\* refusal the script should not have raised.

\* Provenance exists only after compose up, and after a Caddy reload when the
\* service is caddy. A refused step does not write the JSON file.
ProvenanceFollowsUp ==
  provenance =>
    /\ compose = "ok"
    /\ refusal = ""
    /\ situation.service # "caddy" \/ situation.caddyReload = "ok"

\* A dirty tree does not get provenance unless --allow-dirty was passed.
DirtyGateHeld ==
  provenance => ~situation.dirty \/ situation.allowDirty

\* A non-main branch does not get provenance unless --canary was passed.
CanaryGateHeld ==
  provenance => ResolvedBranch(situation) = "main" \/ situation.canary

\* A macmini deploy from another machine does not get provenance unless
\* --allow-foreign-host was passed.
ForeignHostGateHeld ==
  provenance /\ situation.host = "macmini" /\ ~situation.onProductionHost =>
    situation.allowForeignHost

\* nasfeo never takes the macmini identity refusal.
NasfeoSkipsIdentity ==
  situation.host = "nasfeo" => refusal # "foreign"

\* A named main checkout is not refused as a branch deploy. GITHUB_REF_NAME
\* does not replace it, including a pull_request ref such as 50/merge.
NamedMainIsMain ==
  refusal = "canary" => situation.namedBranch # "main"

\* A named feature checkout still needs --canary when GITHUB_REF_NAME is main.
FeatureCheckoutNeedsCanary ==
  situation.namedBranch = "feature" /\ provenance => situation.canary

\* Detached HEAD is not main when the job ref is missing or is 50/merge.
DetachedHeadIsNotMain ==
  /\ situation.namedBranch = "detached"
  /\ situation.githubRefName \in {"", "50/merge"}
  /\ provenance
  => situation.canary

\* Real provenance follows a passing strict config check, or the operator
\* passed --skip-config-validate. A missing validator is not that flag.
ConfigProof ==
  provenance => configProof \in {"passed", "skipped_flag"}

\* --dry-run does not pull, start containers, or write provenance.
DryRunWritesNothing ==
  situation.dryRun => ~provenance /\ pull = "unreached" /\ compose = "unreached"

\* An auth, denied, missing, or unknown-manifest pull does not start containers.
AuthPullDoesNotStart ==
  pull = "auth" => compose = "unreached" /\ ~provenance

\* A non-zero prepare_service does not pull, start containers, or write
\* provenance. Dry-run returns before the generator, so it is not this case.
PrepareFailureStops ==
  situation.prepare = "fail" /\ ~situation.dryRun =>
    /\ pull = "unreached"
    /\ compose = "unreached"
    /\ ~provenance

\* Caddy does not pull, including when its image is ghcr.io/feocco/*.
CaddyDoesNotPull ==
  situation.service = "caddy" /\ pull # "unreached" => pull = "skipped_caddy"

\* A compose file with no ghcr.io/feocco image is not explicitly pulled.
ThirdPartyDoesNotPull ==
  situation.service # "caddy" /\ situation.imageOwner = "third" /\ pull # "unreached" =>
    pull = "skipped_third_party"

\* A service listed in .render-env-skipped is not validated, pulled, started,
\* or recorded. --skip-config-validate does not skip this refusal.
SecretsBlockTheDeploy ==
  situation.secretsSkipped =>
    /\ configProof = "unreached"
    /\ pull = "unreached"
    /\ compose = "unreached"
    /\ ~provenance

\* The JSON dirty and canary fields are the tree and the flag, not a guess.
ProvenanceRecordsFlags ==
  provenance =>
    /\ recordedDirty = situation.dirty
    /\ recordedCanary = situation.canary

\* A finished invocation refused, wrote provenance, or was a dry-run.
EveryStopIsExplained ==
  pc = "done" => provenance \/ refusal # "" \/ situation.dryRun

====
