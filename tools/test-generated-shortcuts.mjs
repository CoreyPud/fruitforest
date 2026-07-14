#!/usr/bin/env node

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const generatedFiles = [
  "shortcuts/generated/Echo Quick Play.unsigned.json",
  "shortcuts/generated/Play on Echo.unsigned.json",
];

for (const file of generatedFiles) {
  const workflow = JSON.parse(readFileSync(new URL(`../${file}`, import.meta.url)));
  const requests = workflow.WFWorkflowActions.filter(
    (action) => action.WFWorkflowActionIdentifier === "is.workflow.actions.downloadurl",
  );
  const targetReads = requests.filter(
    (action) => action.WFWorkflowActionParameters.WFHTTPMethod === "GET",
  );
  const playbackPosts = requests.filter(
    (action) => action.WFWorkflowActionParameters.WFHTTPMethod === "POST",
  );

  assert.ok(targetReads.length >= 1, `${file} must fetch FruitForest targets`);
  assert.ok(playbackPosts.length >= 1, `${file} must POST a playback request`);
  assert.ok(
    targetReads.every(
      (action) => action.WFWorkflowActionParameters.WFURL !== undefined,
    ),
    `${file} target requests must include the webhook URL`,
  );

  const staticRoomLists = workflow.WFWorkflowActions.filter(
    (action) =>
      action.WFWorkflowActionIdentifier === "is.workflow.actions.list" &&
      action.WFWorkflowActionParameters.WFItems?.some((item) =>
        ["kitchen", "office", "masterbedroom", "everywhere"].includes(item),
      ),
  );
  assert.equal(staticRoomLists.length, 0, `${file} must not contain static rooms`);

  const actionUuids = workflow.WFWorkflowActions.flatMap((action) => {
    const uuid = action.WFWorkflowActionParameters?.UUID;
    return uuid ? [uuid] : [];
  });
  assert.equal(
    new Set(actionUuids).size,
    actionUuids.length,
    `${file} must not reuse an action output UUID`,
  );
}

const buildWithFreshUuids = () => {
  const outputDir = mkdtempSync(join(tmpdir(), "fruitforest-shortcuts-"));
  execFileSync(process.execPath, ["tools/generate-shortcuts.mjs"], {
    env: {
      ...process.env,
      PLAY_ON_ECHO_OUTPUT_DIR: outputDir,
      PLAY_ON_ECHO_RANDOMIZE_UUIDS: "1",
    },
    stdio: "ignore",
  });
  return JSON.parse(
    readFileSync(join(outputDir, "Play on Echo.unsigned.json"), "utf8"),
  );
};

const collectDefinedUuids = (workflow) =>
  workflow.WFWorkflowActions.flatMap((action) => {
    const parameters = action.WFWorkflowActionParameters || {};
    const groupingUuid =
      parameters.WFControlFlowMode === 0 ? parameters.GroupingIdentifier : null;
    return [parameters.UUID, groupingUuid].filter(Boolean);
  });

const firstPrivateUuids = collectDefinedUuids(buildWithFreshUuids());
const secondPrivateUuids = collectDefinedUuids(buildWithFreshUuids());
const secondPrivateUuidSet = new Set(secondPrivateUuids);

assert.equal(
  new Set(firstPrivateUuids).size,
  firstPrivateUuids.length,
  "private builds must not reuse an action or control-flow UUID",
);
assert.equal(
  firstPrivateUuids.some((uuid) => secondPrivateUuidSet.has(uuid)),
  false,
  "separate private builds must use disjoint UUIDs for reliable iCloud imports",
);

console.log(`Validated ${generatedFiles.length} dynamic FruitForest shortcuts.`);
