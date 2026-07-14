#!/usr/bin/env node

import { writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const outDir = process.env.PLAY_ON_ECHO_OUTPUT_DIR
  ? new URL(`file://${process.env.PLAY_ON_ECHO_OUTPUT_DIR.replace(/\/$/, "")}/`)
  : new URL("../shortcuts/generated/", import.meta.url);
mkdirSync(outDir, { recursive: true });

const webhookUrl =
  process.env.PLAY_ON_ECHO_WEBHOOK_URL ||
  "http://YOUR_HA_HOST:8123/api/webhook/REPLACE_WITH_LONG_RANDOM_ID";
const sender = process.env.PLAY_ON_ECHO_SENDER || "";
const targets = (process.env.PLAY_ON_ECHO_TARGETS || "kitchen,office,masterbedroom,everywhere")
  .split(",")
  .map((target) => target.trim())
  .filter(Boolean);

const token = (string, attachmentsByRange = {}) => ({
  WFSerializationType: "WFTextTokenString",
  Value: { string, attachmentsByRange },
});

const actionOutput = (name) => ({
  WFSerializationType: "WFTextTokenAttachment",
  Value: {
    Type: "ActionOutput",
    OutputUUID: crypto.randomUUID(),
    ...(name ? { OutputName: name } : {}),
  },
});

const variable = (name) => ({
  WFSerializationType: "WFTextTokenAttachment",
  Value: { Type: "Variable", VariableName: name },
});

const textWith = (parts, ...vars) => {
  const string = parts.join("\uFFFC");
  const attachmentsByRange = {};
  let position = 0;

  for (let i = 0; i < vars.length; i += 1) {
    position += parts[i].length;
    attachmentsByRange[`{${position}, 1}`] = vars[i].Value;
    position += 1;
  }

  return token(string, attachmentsByRange);
};

const textParam = (value) => {
  if (typeof value === "string" || value.WFSerializationType === "WFTextTokenString") {
    return value;
  }

  return textWith`${value}`;
};

const field = (key, value) => ({
  WFItemType: 0,
  WFKey: token(key),
  WFValue: typeof value === "string" ? token(value) : value,
});

const dictionaryValue = (fields) => ({
  WFSerializationType: "WFDictionaryFieldValue",
  Value: { WFDictionaryFieldValueItems: fields },
});

const action = (id, parameters = {}) => ({
  WFWorkflowActionIdentifier: id,
  WFWorkflowActionParameters: parameters,
});

const withOutput = (shortcutAction, output) => {
  shortcutAction.WFWorkflowActionParameters.UUID = output.Value.OutputUUID;
  if (output.Value.OutputName) {
    shortcutAction.WFWorkflowActionParameters.CustomOutputName = output.Value.OutputName;
  }
  return shortcutAction;
};

const ask = ({ prompt, inputType = "Text", output }) =>
  withOutput(
    action("is.workflow.actions.ask", {
      WFInputType: inputType,
      WFAskActionPrompt: prompt,
    }),
    output,
  );

const list = (items, output = null) => {
  const shortcutAction = action("is.workflow.actions.list", {
    WFItems: items,
  });
  return output ? withOutput(shortcutAction, output) : shortcutAction;
};

const chooseFromList = ({ prompt, input = null, output }) =>
  withOutput(
    action("is.workflow.actions.choosefromlist", {
      WFChooseFromListActionPrompt: prompt,
      WFChooseFromListActionSelectMultiple: false,
      ...(input ? { WFInput: input } : {}),
    }),
    output,
  );

const url = (value) =>
  action("is.workflow.actions.url", {
    WFURLActionURL: typeof value === "string" ? value : value,
  });

const getContents = ({ url: requestUrl = null, method = "GET", jsonFields = null, output = null } = {}) => {
  const parameters = {
    Advanced: method !== "GET",
    WFHTTPMethod: method,
    WFHTTPBodyType: "JSON",
  };

  if (requestUrl) {
    parameters.WFURL = textParam(requestUrl);
  }

  if (jsonFields) {
    parameters.WFJSONValues = dictionaryValue(jsonFields);
  }

  const shortcutAction = action("is.workflow.actions.downloadurl", parameters);
  return output ? withOutput(shortcutAction, output) : shortcutAction;
};

const showNotification = ({ title, body }) =>
  action("is.workflow.actions.notification", {
    WFNotificationActionTitle: title,
    WFNotificationActionBody: body,
    WFNotificationActionSound: true,
  });

const getVariable = (name) =>
  action("is.workflow.actions.getvariable", {
    WFVariable: variable(name),
  });

const getMagicVariable = (magicVariable) =>
  action("is.workflow.actions.getvariable", {
    WFVariable: magicVariable,
  });

const setVariable = (name, input = null) =>
  action("is.workflow.actions.setvariable", {
    WFVariableName: name,
    ...(input ? { WFInput: input } : {}),
  });

const text = (value, output = null) => {
  const shortcutAction = action("is.workflow.actions.gettext", {
    WFTextActionText: typeof value === "string" ? value : value,
  });

  return output ? withOutput(shortcutAction, output) : shortcutAction;
};

const setTextVariable = (name, value) => {
  const output = actionOutput(`${name} value`);
  return [text(value, output), setVariable(name, output)];
};

const nothing = () => action("is.workflow.actions.nothing");

const matchText = ({ pattern, input = null, output }) =>
  withOutput(
    action("is.workflow.actions.text.match", {
      WFMatchTextPattern: pattern,
      WFMatchTextCaseSensitive: false,
      ...(input ? { text: textParam(input) } : {}),
    }),
    output,
  );

const countItems = ({ input = null, output = null } = {}) => {
  const shortcutAction = action("is.workflow.actions.count", {
    WFCountType: "Items",
    ...(input ? { Input: input } : {}),
  });
  return output ? withOutput(shortcutAction, output) : shortcutAction;
};

const getFirstItem = ({ input = null, output }) =>
  withOutput(
    action("is.workflow.actions.getitemfromlist", {
      WFItemSpecifier: "First Item",
      ...(input ? { WFInput: input } : {}),
    }),
    output,
  );

const getMatchGroup = ({ index = "1", input = null, output }) =>
  withOutput(
    action("is.workflow.actions.text.match.getgroup", {
      WFGetGroupType: "Group At Index",
      WFGroupIndex: String(index),
      ...(input ? { matches: input } : {}),
    }),
    output,
  );

const getDictionaryFromInput = ({ input = null, output = null } = {}) => {
  const shortcutAction = action("is.workflow.actions.detect.dictionary", {
    ...(input ? { WFInput: input } : {}),
  });
  return output ? withOutput(shortcutAction, output) : shortcutAction;
};

const getDictionaryValue = ({ key, input = null, output }) =>
  withOutput(
    action("is.workflow.actions.getvalueforkey", {
      WFDictionaryKey: key,
      WFGetDictionaryValueType: "Value",
      ...(input ? { WFInput: input } : {}),
    }),
    output,
  );

const replaceText = ({ find, replace = "", regex = false, input = null, output }) =>
  withOutput(
    action("is.workflow.actions.text.replace", {
      WFReplaceTextFind: find,
      WFReplaceTextReplace: replace,
      WFReplaceTextRegularExpression: regex,
      WFReplaceTextCaseSensitive: false,
      ...(input ? { text: textParam(input) } : {}),
    }),
    output,
  );

const conditional = ({ input = null, numberValue = 0, ifTrue = [], ifFalse = [] }) => {
  const group = crypto.randomUUID();
  return [
    action("is.workflow.actions.conditional", {
      GroupingIdentifier: group,
      WFControlFlowMode: 0,
      WFCondition: 2,
      WFNumberValue: String(numberValue),
      ...(input ? { WFInput: { Type: "Variable", Variable: input } } : {}),
    }),
    ...ifTrue,
    ...(ifFalse.length
      ? [
          action("is.workflow.actions.conditional", {
            GroupingIdentifier: group,
            WFControlFlowMode: 1,
          }),
          ...ifFalse,
        ]
      : []),
    action("is.workflow.actions.conditional", {
      GroupingIdentifier: group,
      WFControlFlowMode: 2,
    }),
  ];
};

const shortcutInput = {
  WFSerializationType: "WFTextTokenAttachment",
  Value: { Type: "ExtensionInput" },
};

const getUrlsFromInput = ({ input = null, output }) =>
  withOutput(
    action("is.workflow.actions.detect.link", {
      ...(input ? { WFInput: input } : {}),
    }),
    output,
  );

const getCurrentSong = (output) =>
  withOutput(action("is.workflow.actions.getcurrentsong"), output);

const getMusicProperty = ({ property, input, output }) =>
  withOutput(
    action("is.workflow.actions.properties.music", {
      WFContentItemPropertyName: property,
      WFInput: input,
    }),
    output,
  );

const expandUrl = ({ input = null, output }) =>
  withOutput(
    action("is.workflow.actions.url.expand", {
      ...(input ? { URL: textParam(input) } : {}),
    }),
    output,
  );

const lookupBranch = ({ matches, idOutputName, titleKey, kind }) => {
  const itemId = actionOutput(idOutputName);
  const lookupResponse = actionOutput(`${kind} lookup response`);
  const lookupDictionary = actionOutput(`${kind} lookup dictionary`);
  const lookupResults = actionOutput(`${kind} results`);
  const lookupItem = actionOutput(`${kind} lookup item`);
  const titleValue = actionOutput(`${kind} title`);
  const artistValue = actionOutput(`${kind} artist`);

  return [
    getFirstItem({ input: matches, output: itemId }),
    getContents({ url: textWith`https://itunes.apple.com/lookup?id=${itemId}`, output: lookupResponse }),
    getDictionaryFromInput({ input: lookupResponse, output: lookupDictionary }),
    getDictionaryValue({ key: "results", input: lookupDictionary, output: lookupResults }),
    getFirstItem({ input: lookupResults, output: lookupItem }),
    setVariable("Lookup Item", lookupItem),
    getDictionaryValue({ key: titleKey, input: variable("Lookup Item"), output: titleValue }),
    setVariable("Title", titleValue),
    getDictionaryValue({ key: "artistName", input: variable("Lookup Item"), output: artistValue }),
    setVariable("Artist", artistValue),
    ...setTextVariable("Kind", "track" === kind ? "track" : kind),
  ];
};

const postActions = ({ titleSource, targetSource, bodyLabel }) => {
  const playbackTargets = actionOutput("Playback targets");
  return [
    list(targets, playbackTargets),
    chooseFromList({ prompt: "Play where?", input: playbackTargets, output: targetSource }),
    getContents({
    url: webhookUrl,
    method: "POST",
    jsonFields: [
      field("kind", textWith`${variable("Kind")}`),
      field("title", titleSource || textWith`${variable("Title")}`),
      field("artist", textWith`${variable("Artist")}`),
      field("name", textWith`${variable("Name")}`),
      field("target", textWith`${targetSource}`),
      field("sender", sender),
    ],
    }),
    showNotification({
      title: "Sent to Echo",
      body: bodyLabel || textWith`${variable("Kind")}: ${variable("Title")}${variable("Name")} -> ${targetSource}`,
    }),
  ];
};

const quickCommand = () => {
  const providedInput = actionOutput("Provided Input");
  const chosenTarget = actionOutput("Chosen Item");
  const playbackTargets = actionOutput("Playback targets");

  return workflow({
    actions: [
      ask({ prompt: "Play what?", output: providedInput }),
      list(targets, playbackTargets),
      chooseFromList({ prompt: "Play where?", input: playbackTargets, output: chosenTarget }),
      getContents({
        url: webhookUrl,
        method: "POST",
        jsonFields: [
          field("kind", "freeform"),
          field("title", textWith`${providedInput}`),
          field("target", textWith`${chosenTarget}`),
          field("sender", sender),
        ],
      }),
      showNotification({
        title: "Sent to Echo",
        body: textWith`${providedInput} -> ${chosenTarget}`,
      }),
    ],
  });
};

const playOnEcho = () => {
  const sharedUrls = actionOutput("Shared URLs");
  const sharedUrlCount = actionOutput("Shared URL count");
  const trackMatches = actionOutput("Track matches");
  const trackMatchCount = actionOutput("Track match count");
  const albumMatches = actionOutput("Album matches");
  const albumMatchCount = actionOutput("Album match count");
  const playlistMatches = actionOutput("Playlist matches");
  const playlistMatchCount = actionOutput("Playlist match count");
  const playlistName = actionOutput("Playlist name");
  const playlistMetadata = actionOutput("Playlist metadata");
  const chosenTarget = actionOutput("Chosen Item");
  const sharedUrlInput = actionOutput("Shared URL Input");
  const appleMusicPage = actionOutput("Apple Music page");
  const currentSong = actionOutput("Current Song");
  const currentSongCount = actionOutput("Current Song count");
  const currentAlbum = actionOutput("Current Album");
  const currentArtist = actionOutput("Current Artist");

  const routeActions = [
    getFirstItem({ input: sharedUrls, output: sharedUrlInput }),
    matchText({
      pattern: "(?<=[?&]i=)\\d+",
      input: sharedUrlInput,
      output: trackMatches,
    }),
    countItems({ input: trackMatches, output: trackMatchCount }),
    ...conditional({
      input: trackMatchCount,
      ifTrue: lookupBranch({
        matches: trackMatches,
        idOutputName: "Track ID",
        titleKey: "trackName",
        kind: "track",
      }),
      ifFalse: [
        matchText({
          pattern: "(?<=/)\\d+(?=\\?|$)",
          input: sharedUrlInput,
          output: albumMatches,
        }),
        countItems({ input: albumMatches, output: albumMatchCount }),
        ...conditional({
          input: albumMatchCount,
          ifTrue: lookupBranch({
            matches: albumMatches,
            idOutputName: "Album ID",
            titleKey: "collectionName",
            kind: "album",
          }),
          ifFalse: [
            matchText({ pattern: "/playlist/", input: sharedUrlInput, output: playlistMatches }),
            countItems({ input: playlistMatches, output: playlistMatchCount }),
            ...conditional({
              input: playlistMatchCount,
              ifTrue: [
                getContents({
                  url: textWith`https://music.apple.com/api/oembed?url=${sharedUrlInput}`,
                  output: appleMusicPage,
                }),
                getDictionaryFromInput({ input: appleMusicPage, output: playlistMetadata }),
                getDictionaryValue({ key: "title", input: playlistMetadata, output: playlistName }),
                setVariable("Name", playlistName),
                ...setTextVariable("Kind", "playlist"),
              ],
              ifFalse: [
                setVariable("Title", sharedUrlInput),
                ...setTextVariable("Kind", "freeform"),
              ],
            }),
          ],
        }),
      ],
    }),
    ...postActions({ targetSource: chosenTarget }),
  ];

  const currentSongFallback = [
    getCurrentSong(currentSong),
    countItems({ input: currentSong, output: currentSongCount }),
    ...conditional({
      input: currentSongCount,
      ifTrue: [
        getMusicProperty({ property: "Album", input: currentSong, output: currentAlbum }),
        setVariable("Title", currentAlbum),
        getMusicProperty({ property: "Artist", input: currentSong, output: currentArtist }),
        setVariable("Artist", currentArtist),
        ...setTextVariable("Kind", "album"),
        ...postActions({ targetSource: chosenTarget }),
      ],
      ifFalse: [
        showNotification({
          title: "Nothing sent",
          body: "No link or current Apple Music song was available. Start a song from the album, then share again.",
        }),
      ],
    }),
  ];

  return workflow({
    workflowTypes: ["ActionExtension"],
    inputClasses: [
      "WFAppContentItem",
      "WFAppStoreAppContentItem",
      "WFArticleContentItem",
      "WFContactContentItem",
      "WFDateContentItem",
      "WFEmailAddressContentItem",
      "WFFolderContentItem",
      "WFGenericFileContentItem",
      "WFImageContentItem",
      "WFiTunesProductContentItem",
      "WFLocationContentItem",
      "WFDCMapsLinkContentItem",
      "WFAVAssetContentItem",
      "WFPDFContentItem",
      "WFPhoneNumberContentItem",
      "WFRichTextContentItem",
      "WFSafariWebPageContentItem",
      "WFStringContentItem",
      "WFURLContentItem",
    ],
    actions: [
      getUrlsFromInput({ output: sharedUrls }),
      nothing(),
      setVariable("Title"),
      nothing(),
      setVariable("Artist"),
      nothing(),
      setVariable("Name"),
      ...setTextVariable("Kind", "freeform"),
      countItems({ input: sharedUrls, output: sharedUrlCount }),
      ...conditional({
        input: sharedUrlCount,
        ifTrue: routeActions,
        ifFalse: currentSongFallback,
      }),
    ],
  });
};

function workflow({ actions, workflowTypes = [], inputClasses = [] }) {
  return {
    WFWorkflowClientVersion: "3107",
    WFWorkflowClientRelease: "26.0",
    WFWorkflowIcon: {
      WFWorkflowIconStartColor: 4274264319,
      WFWorkflowIconGlyphNumber: 61440,
    },
    WFWorkflowImportQuestions: [],
    WFWorkflowTypes: workflowTypes,
    WFWorkflowInputContentItemClasses: inputClasses,
    ...(workflowTypes.includes("ActionExtension")
      ? { WFWorkflowHasShortcutInputVariables: true }
      : {}),
    WFWorkflowActions: actions,
  };
}

const files = [
  ["Echo Quick Play.unsigned.json", quickCommand()],
  ["Play on Echo.unsigned.json", playOnEcho()],
];

for (const [name, data] of files) {
  writeFileSync(join(outDir.pathname, name), JSON.stringify(data, null, 2));
}

console.log(`Generated ${files.length} shortcut source files in ${outDir.pathname}`);
