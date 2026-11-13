// Chart of one homelab-deploy invocation. Labels are what the operator sees.

// Same rule as ResolvedBranch in HomelabDeploy.tla (git_branch).
function resolvedBranch(s) {
  if (s.namedBranch === "detached" && s.githubRefName !== "") return s.githubRefName;
  if (s.namedBranch !== "detached") return s.namedBranch;
  return "HEAD";
}

const phases = {
  start: "Start",
  dirty: "Dirty-worktree gate",
  identity: "Mac mini host gate",
  canary: "Branch gate",
  secrets: "Secrets gate",
  config: "Config validation",
  prepare: "Prepare",
  pull: "Image pull",
  compose: "Compose up",
  reload: "Caddy reload",
  record: "Write provenance",
};

const refusals = {
  dirty: "Refused: dirty worktree",
  foreign: "Refused: not the Mac mini",
  canary: "Refused: branch needs canary",
  secrets: "Refused: secrets missing",
  config: "Refused: config validation",
  prepare: "Refused: prepare failed",
  pull_auth: "Refused: image pull denied",
  compose: "Refused: compose up failed",
  reload: "Refused: Caddy reload failed",
};

export const title = "Homelab deploy";

export function state(v) {
  if (v.pc === "done") {
    if (v.provenance && v.configProof === "skipped_absent") {
      return "Provenance without config proof";
    }
    if (v.provenance) return "Provenance written";
    if (v.refusal && refusals[v.refusal]) return refusals[v.refusal];
    if (v.situation.dryRun) return "Dry run finished";
    return "Stopped";
  }
  return phases[v.pc] || v.pc;
}

export function step(action, from, to) {
  if (action === "Done") return null;
  const src = state(from);
  const dst = state(to);
  if (src === "Start" && dst === "Dirty-worktree gate") return "real deploy";
  if (src === "Start" && dst === "Secrets gate") return "dry run";
  if (src === "Dirty-worktree gate" && dst === "Mac mini host gate") {
    return from.situation.dirty ? "continue [--allow-dirty]" : "continue [clean tree]";
  }
  if (dst === "Refused: dirty worktree") return "refuse the dirty worktree";
  if (src === "Mac mini host gate" && dst === "Branch gate") {
    if (from.situation.host !== "macmini") return "continue [nasfeo]";
    if (from.situation.allowForeignHost) return "continue [--allow-foreign-host]";
    return "continue [this machine is the Mac mini]";
  }
  if (dst === "Refused: not the Mac mini") return "refuse the other machine";
  if (src === "Branch gate" && dst === "Secrets gate") {
    if (resolvedBranch(from.situation) === "main") return "continue [branch is main]";
    if (from.situation.canary) return "continue [--canary]";
    return "continue without --canary";
  }
  if (dst === "Refused: branch needs canary") return "refuse the branch deploy";
  if (src === "Secrets gate" && dst === "Config validation") return "secrets are present";
  if (dst === "Refused: secrets missing") return "refuse missing secrets";
  if (src === "Config validation" && dst === "Prepare") {
    if (from.situation.dryRun) return "skip validation [dry run]";
    if (from.situation.skipConfigValidate) return "skip validation [--skip-config-validate]";
    if (from.situation.validator === "absent") return "validator or python3 is missing";
    return "validation passed";
  }
  if (dst === "Refused: config validation") return "validation failed";
  if (src === "Prepare" && dst === "Image pull") return "prepare finished";
  if (dst === "Dry run finished") return "stop before pull and compose";
  if (dst === "Refused: prepare failed") return "prepare failed";
  if (src === "Image pull" && dst === "Compose up") {
    if (to.pull === "skipped_caddy") return "skip the pull [Caddy is built locally]";
    if (to.pull === "skipped_third_party") return "skip the pull [no ghcr.io/feocco image]";
    if (to.pull === "transient") return "keep the cached image [transient pull error]";
    return "pull the ghcr.io/feocco image";
  }
  if (dst === "Refused: image pull denied") {
    return "the image pull was denied or the image does not exist";
  }
  if (src === "Compose up" && dst === "Caddy reload") return "Caddy is up";
  if (dst === "Refused: compose up failed") return "compose up failed";
  if (src === "Caddy reload" && dst === "Write provenance") return "Caddy reloaded";
  if (dst === "Refused: Caddy reload failed") return "Caddy rejected the Caddyfile";
  if (src === "Compose up" && dst === "Write provenance") return "containers are up";
  if (dst === "Provenance without config proof") return "record the deploy without config proof";
  if (dst === "Provenance written") return "record the deploy";
  return null;
}

export function group(v) {
  const label = state(v);
  if (label === "Provenance without config proof") return "finding";
  if (label.startsWith("Refused")) return "refused";
  if (label === "Dry run finished") return "dry";
  if (label === "Provenance written") return "deployed";
  if (
    label === "Prepare" ||
    label === "Image pull" ||
    label === "Compose up" ||
    label === "Caddy reload" ||
    label === "Write provenance"
  ) {
    return "rollout";
  }
  return "gates";
}

export const colors = {
  gates: "blue",
  rollout: "teal",
  deployed: "purple",
  refused: "orange",
  dry: "tan",
  finding: "pink",
};
