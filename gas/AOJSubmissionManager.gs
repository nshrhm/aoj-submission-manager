var AOJ_SHEETS = {
  STUDENTS: 'Students',
  PROBLEMS: 'Problems',
  BEST: 'BestSubmissions',
  DASHBOARD: 'Dashboard',
  RANKINGS: 'Rankings',
  SETTINGS: 'Settings'
};

var AOJ_HEADERS = {
  students: ['studentId', 'surname', 'givenName', 'aojUserId'],
  problems: ['problemId'],
  best: ['studentId', 'problemId', 'score', 'submissionDateMs', 'judgeId', 'updatedAt']
};

var AOJ_DEFAULTS = {
  noSubmission: -1,
  acceptedScore: 100,
  endpoint: 'https://judgeapi.u-aizu.ac.jp',
  syncCursorProperty: 'AOJ_SYNC_CURSOR',
  settings: [
    ['key', 'value', 'description'],
    ['requestChunkSize', '40', 'UrlFetchApp.fetchAll でまとめて叩くリクエスト数'],
    ['maxExecutionMs', '330000', '1 回の実行で使う最大ミリ秒'],
    ['autoRebuildAfterSync', 'TRUE', '同期完了後に Dashboard/Rankings を自動再構築する'],
    ['snapshotBeforeMutation', 'TRUE', '更新系処理の前に BestSubmissions の CSV スナップショットを保存する'],
    ['exportFolderId', '', 'TSV の保存先 Drive フォルダ ID。空ならマイドライブ直下'],
    ['codeFolderId', '', '100 点コードの保存先 Drive フォルダ ID。空ならマイドライブ直下'],
    ['snapshotFolderId', '', 'スナップショット CSV の保存先 Drive フォルダ ID。空ならマイドライブ直下'],
    ['dashboardTimestampFormat', 'yyyy/MM/dd HH:mm:ss', 'Dashboard に表示する日時フォーマット']
  ]
};

function onOpen() {
  ensureWorkbook_();
  SpreadsheetApp.getUi()
    .createMenu('AOJ Manager')
    .addItem('AOJ Sync', 'syncAojSubmissions')
    .addItem('Initialize Data', 'initializeData')
    .addItem('Normalize Data', 'normalizeData')
    .addItem('Rebuild Dashboard', 'rebuildDashboard')
    .addItem('Rebuild Rankings', 'rebuildRankings')
    .addSeparator()
    .addItem('Export TSV', 'exportTsv')
    .addItem('Download Accepted Code', 'downloadAcceptedCode')
    .addToUi();
}

function initializeData() {
  ensureWorkbook_();
  createSnapshotIfEnabled_('initialize');

  var students = readStudents_();
  var problems = readProblems_();
  var rows = [];
  var now = isoNow_();
  var i;
  var j;

  for (i = 0; i < students.length; i += 1) {
    for (j = 0; j < problems.length; j += 1) {
      rows.push([
        students[i].studentId,
        problems[j],
        '0',
        '0',
        String(AOJ_DEFAULTS.noSubmission),
        now
      ]);
    }
  }

  writeBestSubmissionsRows_(rows);
  rebuildDashboard();
  rebuildRankings();
  clearSyncCursor_();
  toast_('BestSubmissions を初期化しました。');
}

function normalizeData() {
  ensureWorkbook_();
  createSnapshotIfEnabled_('normalize');

  var rows = readBestSubmissionsRows_();
  var normalized = [];
  var i;

  for (i = 0; i < rows.length; i += 1) {
    normalized.push(toBestSubmissionRow_(normalizeSubmission_(rowToSubmission_(rows[i]))));
  }

  writeBestSubmissionsRows_(normalized);
  rebuildDashboard();
  rebuildRankings();
  toast_('BestSubmissions を正規化しました。');
}

function syncAojSubmissions() {
  ensureWorkbook_();

  var settings = getSettings_();
  var students = readStudents_();
  var problems = readProblems_();
  var tasks = buildSyncTasks_(students, problems);
  var props = PropertiesService.getScriptProperties();
  var cursor = parseInt(props.getProperty(AOJ_DEFAULTS.syncCursorProperty) || '0', 10);
  var startTime = new Date().getTime();
  var chunkSize = getSettingNumber_(settings, 'requestChunkSize', 40);
  var maxExecutionMs = getSettingNumber_(settings, 'maxExecutionMs', 330000);
  var submissionMap = readBestSubmissionsMap_();
  var updates = {};
  var i;

  if (!tasks.length) {
    toast_('Students または Problems にデータがありません。');
    return;
  }

  if (cursor <= 0 || cursor >= tasks.length) {
    cursor = 0;
    createSnapshotIfEnabled_('sync');
  }

  for (i = 0; i < tasks.length; i += 1) {
    ensureSubmissionExists_(submissionMap, tasks[i].studentId, tasks[i].problemId);
  }

  while (cursor < tasks.length) {
    if ((new Date().getTime() - startTime) >= maxExecutionMs) {
      break;
    }

    processSyncChunk_(tasks.slice(cursor, cursor + chunkSize), submissionMap, updates);
    cursor += chunkSize;
  }

  writeBestSubmissionsMap_(submissionMap);

  if (cursor < tasks.length) {
    props.setProperty(AOJ_DEFAULTS.syncCursorProperty, String(cursor));
    toast_('途中まで同期しました。続きはもう一度 AOJ Sync を実行してください。');
    return;
  }

  clearSyncCursor_();
  if (getSettingBoolean_(settings, 'autoRebuildAfterSync', true)) {
    rebuildDashboard();
    rebuildRankings();
  }

  logSyncSummary_(updates);
  toast_('AOJ Sync が完了しました。');
}

function rebuildDashboard() {
  ensureWorkbook_();
  var values = buildDashboardValues_();
  writeValuesToSheet_(AOJ_SHEETS.DASHBOARD, values);
  toast_('Dashboard を再構築しました。');
}

function rebuildRankings() {
  ensureWorkbook_();
  var values = buildRankingsValues_();
  writeValuesToSheet_(AOJ_SHEETS.RANKINGS, values);
  toast_('Rankings を再構築しました。');
}

function exportTsv() {
  ensureWorkbook_();
  var folder = getFolderFromSetting_('exportFolderId');
  var stamp = fileTimestamp_();
  var dashboardValues = buildDashboardValues_();
  var rankingValues = buildRankingsValues_();

  createFileInFolder_(folder, 'dashboard_' + stamp + '.tsv', toTsv_(dashboardValues), MimeType.PLAIN_TEXT);
  createFileInFolder_(folder, 'rankings_' + stamp + '.tsv', toTsv_(rankingValues), MimeType.PLAIN_TEXT);
  toast_('Dashboard / Rankings の TSV を Drive に出力しました。');
}

function downloadAcceptedCode() {
  ensureWorkbook_();
  var folder = getFolderFromSetting_('codeFolderId');
  var rows = readBestSubmissionsRows_();
  var tasks = [];
  var settings = getSettings_();
  var chunkSize = getSettingNumber_(settings, 'requestChunkSize', 40);
  var startTime = new Date().getTime();
  var maxExecutionMs = getSettingNumber_(settings, 'maxExecutionMs', 330000);
  var downloaded = 0;
  var i;

  for (i = 0; i < rows.length; i += 1) {
    var submission = normalizeSubmission_(rowToSubmission_(rows[i]));
    if (submission.score === AOJ_DEFAULTS.acceptedScore && submission.judgeId > 0) {
      tasks.push(submission);
    }
  }

  for (i = 0; i < tasks.length; i += chunkSize) {
    if ((new Date().getTime() - startTime) >= maxExecutionMs) {
      toast_('コードの保存を途中で止めました。必要なら再実行してください。');
      return;
    }

    downloaded += processCodeChunk_(tasks.slice(i, i + chunkSize), folder);
  }

  toast_(downloaded + ' 件のコードを Drive に保存しました。');
}

function ensureWorkbook_() {
  ensureSheet_(AOJ_SHEETS.STUDENTS, AOJ_HEADERS.students);
  ensureSheet_(AOJ_SHEETS.PROBLEMS, AOJ_HEADERS.problems);
  ensureSheet_(AOJ_SHEETS.BEST, AOJ_HEADERS.best);
  ensureSheet_(AOJ_SHEETS.DASHBOARD, []);
  ensureSheet_(AOJ_SHEETS.RANKINGS, []);
  ensureSettingsSheet_();
}

function ensureSheet_(sheetName, header) {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName(sheetName);

  if (!sheet) {
    sheet = spreadsheet.insertSheet(sheetName);
  }

  if (header && header.length) {
    var existingHeader = [];
    if (sheet.getLastRow() >= 1 && sheet.getLastColumn() >= 1) {
      existingHeader = sheet.getRange(1, 1, 1, Math.max(header.length, sheet.getLastColumn())).getValues()[0];
    }

    if (!arrayStartsWith_(existingHeader, header)) {
      sheet.getRange(1, 1, 1, header.length).setValues([header]);
      sheet.setFrozenRows(1);
    }
  }

  return sheet;
}

function ensureSettingsSheet_() {
  var sheet = ensureSheet_(AOJ_SHEETS.SETTINGS, []);
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, AOJ_DEFAULTS.settings.length, AOJ_DEFAULTS.settings[0].length)
      .setValues(AOJ_DEFAULTS.settings);
    sheet.setFrozenRows(1);
    return;
  }

  var values = sheet.getDataRange().getValues();
  var keys = {};
  var i;

  for (i = 1; i < values.length; i += 1) {
    if (values[i][0]) {
      keys[String(values[i][0])] = true;
    }
  }

  for (i = 1; i < AOJ_DEFAULTS.settings.length; i += 1) {
    if (!keys[AOJ_DEFAULTS.settings[i][0]]) {
      sheet.appendRow(AOJ_DEFAULTS.settings[i]);
    }
  }
}

function readStudents_() {
  var sheet = ensureSheet_(AOJ_SHEETS.STUDENTS, AOJ_HEADERS.students);
  var values = readDataRows_(sheet);
  var students = [];
  var i;

  for (i = 0; i < values.length; i += 1) {
    if (!values[i][0] || !values[i][3]) {
      continue;
    }
    students.push({
      studentId: String(values[i][0]).trim(),
      surname: String(values[i][1] || '').trim(),
      givenName: String(values[i][2] || '').trim(),
      aojUserId: String(values[i][3] || '').trim()
    });
  }

  students.sort(function(a, b) {
    return compareStrings_(a.studentId, b.studentId);
  });
  return students;
}

function readProblems_() {
  var sheet = ensureSheet_(AOJ_SHEETS.PROBLEMS, AOJ_HEADERS.problems);
  var values = readDataRows_(sheet);
  var problems = [];
  var seen = {};
  var i;

  for (i = 0; i < values.length; i += 1) {
    var problemId = String(values[i][0] || '').trim();
    if (!problemId || seen[problemId]) {
      continue;
    }
    seen[problemId] = true;
    problems.push(problemId);
  }

  problems.sort(compareStrings_);
  return problems;
}

function readBestSubmissionsRows_() {
  var sheet = ensureSheet_(AOJ_SHEETS.BEST, AOJ_HEADERS.best);
  return readDataRows_(sheet);
}

function readBestSubmissionsMap_() {
  var rows = readBestSubmissionsRows_();
  var map = {};
  var i;

  for (i = 0; i < rows.length; i += 1) {
    var submission = normalizeSubmission_(rowToSubmission_(rows[i]));
    map[submissionKey_(submission.studentId, submission.problemId)] = submission;
  }
  return map;
}

function writeBestSubmissionsRows_(rows) {
  var normalizedRows = [];
  var i;

  for (i = 0; i < rows.length; i += 1) {
    normalizedRows.push(toBestSubmissionRow_(normalizeSubmission_(rowToSubmission_(rows[i]))));
  }

  normalizedRows.sort(compareBestSubmissionRows_);
  writeTable_(AOJ_SHEETS.BEST, AOJ_HEADERS.best, normalizedRows);
}

function writeBestSubmissionsMap_(map) {
  var keys = Object.keys(map).sort(compareStrings_);
  var rows = [];
  var i;

  for (i = 0; i < keys.length; i += 1) {
    rows.push(toBestSubmissionRow_(normalizeSubmission_(map[keys[i]])));
  }

  rows.sort(compareBestSubmissionRows_);
  writeTable_(AOJ_SHEETS.BEST, AOJ_HEADERS.best, rows);
}

function buildSyncTasks_(students, problems) {
  var tasks = [];
  var i;
  var j;

  for (i = 0; i < students.length; i += 1) {
    for (j = 0; j < problems.length; j += 1) {
      tasks.push({
        studentId: students[i].studentId,
        aojUserId: students[i].aojUserId,
        problemId: problems[j]
      });
    }
  }

  return tasks;
}

function processSyncChunk_(tasks, submissionMap, updates) {
  var requests = [];
  var i;

  for (i = 0; i < tasks.length; i += 1) {
    requests.push({
      url: AOJ_DEFAULTS.endpoint + '/submission_records/users/' +
        encodeURIComponent(tasks[i].aojUserId) + '/problems/' +
        encodeURIComponent(tasks[i].problemId),
      muteHttpExceptions: true
    });
  }

  var responses = UrlFetchApp.fetchAll(requests);
  var now = isoNow_();

  for (i = 0; i < responses.length; i += 1) {
    var currentTask = tasks[i];
    var response = responses[i];
    var key = submissionKey_(currentTask.studentId, currentTask.problemId);
    var current = submissionMap[key];
    var candidate = current;

    if (response.getResponseCode() === 200) {
      candidate = bestSubmissionFromPayload_(
        currentTask.studentId,
        currentTask.problemId,
        safeJsonArray_(response.getContentText())
      );
    }

    if (isBetterSubmission_(candidate, current)) {
      candidate.updatedAt = now;
      submissionMap[key] = candidate;
      pushSyncUpdate_(updates, currentTask.problemId, currentTask.studentId);
    }
  }
}

function processCodeChunk_(submissions, folder) {
  var requests = [];
  var downloaded = 0;
  var i;

  for (i = 0; i < submissions.length; i += 1) {
    requests.push({
      url: AOJ_DEFAULTS.endpoint + '/reviews/' + encodeURIComponent(String(submissions[i].judgeId)),
      muteHttpExceptions: true
    });
  }

  var responses = UrlFetchApp.fetchAll(requests);

  for (i = 0; i < responses.length; i += 1) {
    if (responses[i].getResponseCode() !== 200) {
      continue;
    }

    var payload = safeJsonObject_(responses[i].getContentText());
    if (!payload || !payload.sourceCode) {
      continue;
    }

    createOrUpdateFile_(folder, submissions[i].studentId + '_' + submissions[i].problemId + '.py', payload.sourceCode);
    downloaded += 1;
  }

  return downloaded;
}

function buildDashboardValues_() {
  var students = readStudents_();
  var problems = readProblems_();
  var bestMap = readBestSubmissionsMap_();
  var settings = getSettings_();
  var format = getSettingString_(settings, 'dashboardTimestampFormat', 'yyyy/MM/dd HH:mm:ss');
  var values = [];
  var header = ['学籍番号', '氏名'];
  var i;
  var j;

  for (i = 0; i < problems.length; i += 1) {
    header.push(problems[i] + '得点');
    header.push(problems[i] + '提出日時');
  }
  values.push(header);

  for (i = 0; i < students.length; i += 1) {
    var row = [students[i].studentId, joinName_(students[i].surname, students[i].givenName)];
    for (j = 0; j < problems.length; j += 1) {
      var submission = bestMap[submissionKey_(students[i].studentId, problems[j])] ||
        defaultSubmission_(students[i].studentId, problems[j]);
      if (submission.score > 0 && submission.submissionDateMs > 0) {
        row.push(String(submission.score));
        row.push(formatTimestamp_(submission.submissionDateMs, format));
      } else {
        row.push('0');
        row.push('未提出');
      }
    }
    values.push(row);
  }

  return values;
}

function buildRankingsValues_() {
  var students = readStudents_();
  var problems = readProblems_();
  var bestMap = readBestSubmissionsMap_();
  var studentMap = {};
  var values = [];
  var totalRanking;
  var i;

  for (i = 0; i < students.length; i += 1) {
    studentMap[students[i].studentId] = students[i];
  }

  totalRanking = buildTotalRankingRows_(students, problems, bestMap);
  values.push(['総合ランキング']);
  values.push(['順位', '全得点', 'AIZU ID', '姓', '名']);
  for (i = 0; i < totalRanking.length; i += 1) {
    values.push(totalRanking[i]);
  }
  values.push([]);
  values.push(['問題別ランキング']);
  values.push([]);

  for (i = 0; i < problems.length; i += 1) {
    var problemRows = buildProblemRankingRows_(problems[i], students, bestMap, studentMap);
    values.push([problems[i]]);
    values.push(['順位', '提出日時', 'AIZU ID', '姓', '名']);
    Array.prototype.push.apply(values, problemRows);
    values.push([]);
  }

  return values;
}

function buildTotalRankingRows_(students, problems, bestMap) {
  var ranking = [];
  var i;
  var j;

  for (i = 0; i < students.length; i += 1) {
    var total = 0;
    for (j = 0; j < problems.length; j += 1) {
      total += Number(bestMap[submissionKey_(students[i].studentId, problems[j])] ?
        bestMap[submissionKey_(students[i].studentId, problems[j])].score : 0);
    }
    if (total > 0) {
      ranking.push({
        total: total,
        aojUserId: students[i].aojUserId,
        surname: students[i].surname,
        givenName: students[i].givenName
      });
    }
  }

  ranking.sort(function(a, b) {
    if (b.total !== a.total) {
      return b.total - a.total;
    }
    return compareStrings_(a.aojUserId, b.aojUserId);
  });

  var rows = [];
  var currentRank = 0;
  var currentScore = null;

  for (i = 0; i < ranking.length; i += 1) {
    if (currentScore === null || ranking[i].total !== currentScore) {
      currentRank = i + 1;
      currentScore = ranking[i].total;
    }
    rows.push([
      currentRank,
      ranking[i].total,
      ranking[i].aojUserId,
      ranking[i].surname,
      ranking[i].givenName
    ]);
  }

  return rows;
}

function buildProblemRankingRows_(problemId, students, bestMap, studentMap) {
  var ranking = [];
  var i;

  for (i = 0; i < students.length; i += 1) {
    var submission = bestMap[submissionKey_(students[i].studentId, problemId)] ||
      defaultSubmission_(students[i].studentId, problemId);
    if (submission.score > 0 && submission.submissionDateMs > 0) {
      ranking.push({
        submissionDateMs: submission.submissionDateMs,
        aojUserId: students[i].aojUserId,
        surname: studentMap[students[i].studentId].surname,
        givenName: studentMap[students[i].studentId].givenName
      });
    }
  }

  ranking.sort(function(a, b) {
    if (a.submissionDateMs !== b.submissionDateMs) {
      return a.submissionDateMs - b.submissionDateMs;
    }
    return compareStrings_(a.aojUserId, b.aojUserId);
  });

  var rows = [];
  for (i = 0; i < ranking.length; i += 1) {
    rows.push([
      i + 1,
      formatTimestamp_(ranking[i].submissionDateMs, 'yyyy/MM/dd HH:mm:ss'),
      ranking[i].aojUserId,
      ranking[i].surname,
      ranking[i].givenName
    ]);
  }
  return rows;
}

function createSnapshotIfEnabled_(reason) {
  var settings = getSettings_();
  if (!getSettingBoolean_(settings, 'snapshotBeforeMutation', true)) {
    return;
  }

  var rows = readBestSubmissionsRows_();
  if (!rows.length) {
    return;
  }

  var folder = getFolderFromSetting_('snapshotFolderId');
  var values = [AOJ_HEADERS.best].concat(rows);
  createFileInFolder_(folder, 'best_submissions_' + reason + '_' + fileTimestamp_() + '.csv', toCsv_(values), MimeType.CSV);
}

function getSettings_() {
  var sheet = ensureSheet_(AOJ_SHEETS.SETTINGS, []);
  var values = sheet.getDataRange().getValues();
  var settings = {};
  var i;

  for (i = 1; i < values.length; i += 1) {
    if (!values[i][0]) {
      continue;
    }
    settings[String(values[i][0])] = values[i][1];
  }
  return settings;
}

function getFolderFromSetting_(key) {
  var settings = getSettings_();
  var folderId = String(settings[key] || '').trim();
  if (!folderId) {
    return DriveApp.getRootFolder();
  }
  return DriveApp.getFolderById(folderId);
}

function ensureSubmissionExists_(submissionMap, studentId, problemId) {
  var key = submissionKey_(studentId, problemId);
  if (!submissionMap[key]) {
    submissionMap[key] = defaultSubmission_(studentId, problemId);
  }
}

function defaultSubmission_(studentId, problemId) {
  return {
    studentId: String(studentId),
    problemId: String(problemId),
    score: 0,
    submissionDateMs: 0,
    judgeId: AOJ_DEFAULTS.noSubmission,
    updatedAt: ''
  };
}

function rowToSubmission_(row) {
  return {
    studentId: String(row[0] || ''),
    problemId: String(row[1] || ''),
    score: row[2],
    submissionDateMs: row[3],
    judgeId: row[4],
    updatedAt: row[5] || ''
  };
}

function toBestSubmissionRow_(submission) {
  return [
    submission.studentId,
    submission.problemId,
    String(submission.score),
    String(submission.submissionDateMs),
    String(submission.judgeId),
    submission.updatedAt || ''
  ];
}

function normalizeSubmission_(submission) {
  var score = parseInt(submission.score, 10);
  var submissionDateMs = parseInt(submission.submissionDateMs, 10);
  var judgeId = parseInt(submission.judgeId, 10);

  if (isNaN(score) || score < 0 || score > 100) {
    score = 0;
  }
  if (isNaN(submissionDateMs) || submissionDateMs < 0) {
    submissionDateMs = 0;
  }
  if (isNaN(judgeId) || judgeId < AOJ_DEFAULTS.noSubmission) {
    judgeId = AOJ_DEFAULTS.noSubmission;
  }

  return {
    studentId: String(submission.studentId || '').trim(),
    problemId: String(submission.problemId || '').trim(),
    score: score,
    submissionDateMs: submissionDateMs,
    judgeId: judgeId,
    updatedAt: submission.updatedAt ? String(submission.updatedAt) : ''
  };
}

function bestSubmissionFromPayload_(studentId, problemId, payload) {
  var best = defaultSubmission_(studentId, problemId);
  var i;

  for (i = 0; i < payload.length; i += 1) {
    var candidate = normalizeSubmission_({
      studentId: studentId,
      problemId: problemId,
      score: payload[i].score,
      submissionDateMs: payload[i].submissionDate,
      judgeId: payload[i].judgeId,
      updatedAt: ''
    });
    if (isBetterSubmission_(candidate, best)) {
      best = candidate;
    }
  }

  return best;
}

function isBetterSubmission_(candidate, current) {
  var normalizedCandidate = normalizeSubmission_(candidate);
  var normalizedCurrent = normalizeSubmission_(current || defaultSubmission_('', ''));

  if (normalizedCandidate.score > normalizedCurrent.score) {
    return true;
  }
  if (normalizedCandidate.score === normalizedCurrent.score &&
      normalizedCandidate.submissionDateMs > normalizedCurrent.submissionDateMs) {
    return true;
  }
  return false;
}

function writeTable_(sheetName, header, rows) {
  var values = [header].concat(rows);
  writeValuesToSheet_(sheetName, values);
}

function writeValuesToSheet_(sheetName, values) {
  var sheet = ensureSheet_(sheetName, []);
  sheet.clearContents();

  if (!values.length) {
    return;
  }

  sheet.getRange(1, 1, values.length, maxColumnCount_(values)).setValues(padRows_(values));
  if (values[0].length > 0) {
    sheet.setFrozenRows(1);
  }
  autosizeSheet_(sheet, values);
}

function readDataRows_(sheet) {
  if (sheet.getLastRow() <= 1) {
    return [];
  }
  return sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn()).getValues();
}

function formatTimestamp_(timestampMs, format) {
  try {
    if (!timestampMs || Number(timestampMs) <= 0) {
      return '未提出';
    }
    return Utilities.formatDate(new Date(Number(timestampMs)), Session.getScriptTimeZone(), format);
  } catch (error) {
    return '未提出';
  }
}

function safeJsonArray_(text) {
  try {
    var parsed = JSON.parse(text || '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    return [];
  }
}

function safeJsonObject_(text) {
  try {
    var parsed = JSON.parse(text || '{}');
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch (error) {
    return null;
  }
}

function createOrUpdateFile_(folder, fileName, content) {
  var files = folder.getFilesByName(fileName);
  if (files.hasNext()) {
    files.next().setContent(content);
    return;
  }
  folder.createFile(fileName, content, MimeType.PLAIN_TEXT);
}

function createFileInFolder_(folder, fileName, content, mimeType) {
  folder.createFile(Utilities.newBlob(content, mimeType, fileName));
}

function toTsv_(values) {
  return delimitedText_(values, '\t');
}

function toCsv_(values) {
  return delimitedText_(values, ',');
}

function delimitedText_(values, delimiter) {
  var padded = padRows_(values);
  var lines = [];
  var i;
  var j;

  for (i = 0; i < padded.length; i += 1) {
    var row = [];
    for (j = 0; j < padded[i].length; j += 1) {
      row.push(escapeField_(padded[i][j], delimiter));
    }
    lines.push(row.join(delimiter));
  }
  return lines.join('\n');
}

function escapeField_(value, delimiter) {
  var text = String(value === null || typeof value === 'undefined' ? '' : value);
  if (text.indexOf('"') !== -1) {
    text = text.replace(/"/g, '""');
  }
  if (text.indexOf('\n') !== -1 || text.indexOf('\r') !== -1 || text.indexOf(delimiter) !== -1) {
    return '"' + text + '"';
  }
  return text;
}

function logSyncSummary_(updates) {
  var sheet = ensureSheet_(AOJ_SHEETS.SETTINGS, []);
  var keys = Object.keys(updates).sort(compareStrings_);
  if (!keys.length) {
    sheet.getRange('E1:F2').setValues([
      ['lastSync', isoNow_()],
      ['updatedProblems', 'なし']
    ]);
    return;
  }

  var values = [['lastSync', isoNow_()], ['updatedProblems', keys.join(', ')]];
  var row;
  for (row = 0; row < keys.length; row += 1) {
    values.push([keys[row], updates[keys[row]].sort(compareStrings_).join(', ')]);
  }
  sheet.getRange(1, 5, values.length, 2).setValues(values);
}

function pushSyncUpdate_(updates, problemId, studentId) {
  if (!updates[problemId]) {
    updates[problemId] = [];
  }
  updates[problemId].push(studentId);
}

function clearSyncCursor_() {
  PropertiesService.getScriptProperties().deleteProperty(AOJ_DEFAULTS.syncCursorProperty);
}

function submissionKey_(studentId, problemId) {
  return String(studentId) + '\t' + String(problemId);
}

function compareBestSubmissionRows_(a, b) {
  var first = compareStrings_(String(a[0]), String(b[0]));
  if (first !== 0) {
    return first;
  }
  return compareStrings_(String(a[1]), String(b[1]));
}

function compareStrings_(a, b) {
  if (a < b) {
    return -1;
  }
  if (a > b) {
    return 1;
  }
  return 0;
}

function getSettingNumber_(settings, key, fallback) {
  var value = parseInt(settings[key], 10);
  return isNaN(value) ? fallback : value;
}

function getSettingBoolean_(settings, key, fallback) {
  if (typeof settings[key] === 'undefined' || settings[key] === '') {
    return fallback;
  }
  return String(settings[key]).toUpperCase() === 'TRUE';
}

function getSettingString_(settings, key, fallback) {
  if (typeof settings[key] === 'undefined' || settings[key] === '') {
    return fallback;
  }
  return String(settings[key]);
}

function padRows_(values) {
  var width = maxColumnCount_(values);
  var padded = [];
  var i;
  var j;

  for (i = 0; i < values.length; i += 1) {
    var row = [];
    for (j = 0; j < width; j += 1) {
      row.push(typeof values[i][j] === 'undefined' ? '' : values[i][j]);
    }
    padded.push(row);
  }
  return padded;
}

function maxColumnCount_(values) {
  var width = 0;
  var i;
  for (i = 0; i < values.length; i += 1) {
    width = Math.max(width, values[i].length);
  }
  return Math.max(width, 1);
}

function autosizeSheet_(sheet, values) {
  var width = maxColumnCount_(values);
  if (width > 0) {
    sheet.autoResizeColumns(1, width);
  }
}

function arrayStartsWith_(values, prefix) {
  var i;
  if (!values || values.length < prefix.length) {
    return false;
  }
  for (i = 0; i < prefix.length; i += 1) {
    if (String(values[i] || '') !== String(prefix[i])) {
      return false;
    }
  }
  return true;
}

function joinName_(surname, givenName) {
  return String(surname || '').trim() + ' ' + String(givenName || '').trim();
}

function isoNow_() {
  return Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd'T'HH:mm:ssXXX");
}

function fileTimestamp_() {
  return Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd_HHmmss');
}

function toast_(message) {
  SpreadsheetApp.getActiveSpreadsheet().toast(message, 'AOJ Manager', 5);
}
