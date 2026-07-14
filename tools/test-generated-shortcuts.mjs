#!/usr/bin/env node

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

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
}

console.log(`Validated ${generatedFiles.length} dynamic FruitForest shortcuts.`);
