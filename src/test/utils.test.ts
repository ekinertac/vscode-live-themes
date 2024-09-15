import * as assert from 'assert';
import * as vscode from 'vscode';
import alignText, { formatLabel } from '../utils/alignText';
import stripJsonComments from '../utils/strip-json-comments';

suite('Utils Test Suite', () => {
  test('alignText.formatLabel()', () => {
    const label = '$(sync) Syncing | Tests';
    const formattedLabel = formatLabel(label);
    assert.strictEqual(formattedLabel.length, 75);
  });

  test('alignText.formatLabel() with no pipe', () => {
    const label = '$(sync) Syncing Tests';
    const formattedLabel = formatLabel(label);
    assert.strictEqual(formattedLabel.length, label.length);
  });

  test('alignText.formatLabel() with no icon', () => {
    const label = 'Syncing | Tests';
    const formattedLabel = formatLabel(label);
    assert.strictEqual(formattedLabel.length, 68);
  });

  test('alignText.formatLabel() with no icon and no pipe', () => {
    const label = 'Syncing Tests';
    const formattedLabel = formatLabel(label);
    assert.strictEqual(formattedLabel.length, label.length);
  });

  test('alignText.alignText()', () => {
    const labels = [{ label: '$(sync) Syncing | Tests' }];
    const alignedLabels = alignText(labels);

    assert.strictEqual(alignedLabels.length, 1);
    assert.strictEqual(alignedLabels[0].label.length, 75);
  });

  test('alignText.formatLabel() with multiple pipes', () => {
    const label = '$(sync) Syncing | Tests | More | Info';
    const formattedLabel = formatLabel(label);
    assert.strictEqual(formattedLabel.length, 76);
    assert.ok(formattedLabel.includes('Syncing'));
    assert.ok(formattedLabel.includes('Tests'));
    assert.ok(formattedLabel.includes('More'));
    assert.ok(formattedLabel.includes('Info'));
  });

  test('alignText.formatLabel() with long text', () => {
    const label = '$(sync) This is a very long text | That exceeds the maximum length';
    const formattedLabel = formatLabel(label);
    assert.strictEqual(formattedLabel.length, 75);
  });

  test('alignText.formatLabel() with only icon', () => {
    const label = '$(sync)';
    const formattedLabel = formatLabel(label);
    assert.strictEqual(formattedLabel, '$(sync)');
  });

  test('alignText.alignText() with multiple labels', () => {
    const labels = [
      { label: '$(sync) Syncing | Tests' },
      { label: '$(fool) Completed | Task' },
      { label: '$(baar) Error | Message' },
    ];
    const alignedLabels = alignText(labels);

    assert.strictEqual(alignedLabels.length, 3);
    alignedLabels.forEach((label) => {
      assert.strictEqual(label.label.length, 75);
    });
  });

  test('alignText.alignText() with mixed label types', () => {
    const labels = [
      { label: '$(sync) Syncing | Tests' },
      { label: 'No icon or pipe' },
      { label: '$(check) Completed' },
    ];
    const alignedLabels = alignText(labels);

    assert.strictEqual(alignedLabels.length, 3);
    assert.strictEqual(alignedLabels[0].label.length, 75);
    assert.strictEqual(alignedLabels[1].label, labels[1].label);
    assert.strictEqual(alignedLabels[2].label, labels[2].label);
  });

  test('stripJsonComments.stripJsonComments() simple json without issues', () => {
    const jsonString = '{"name": "John", "age": 30, "city": "New York"}';
    const strippedJsonString = JSON.parse(stripJsonComments(jsonString));
    assert.deepStrictEqual(strippedJsonString, { name: 'John', age: 30, city: 'New York' });
  });

  test('stripJsonComments.stripJsonComments() simple json with line comment', () => {
    const jsonString = `{
      "name": "John",
      "age": 30, // This is a comment
      "city": "New York"
    }`;
    const strippedJsonString = JSON.parse(stripJsonComments(jsonString));
    const expectedJsonString = {
      name: 'John',
      age: 30,
      city: 'New York',
    };

    assert.deepStrictEqual(strippedJsonString, expectedJsonString);
  });

  test('stripJsonComments.stripJsonComments() simple json with block comment', () => {
    const jsonString = `{
      "name": "John",
      "age": 30, /* This is a block comment */
      "city": "New York"
    }`;
    const strippedJsonString = JSON.parse(stripJsonComments(jsonString));
    const expectedJsonString = {
      name: 'John',
      age: 30,
      city: 'New York',
    };

    assert.deepStrictEqual(strippedJsonString, expectedJsonString);
  });

  test('stripJsonComments.stripJsonComments() simple json with trailing comma', () => {
    const jsonString = `{
      "name": "John", // This is a comment
      "age": 30, /* This is a block comment */
      "city": "New York",
    }`;
    const strippedJsonString = JSON.parse(stripJsonComments(jsonString, { whitespace: false, trailingCommas: true }));
    const expectedJsonString = {
      name: 'John',
      age: 30,
      city: 'New York',
    };

    assert.deepStrictEqual(strippedJsonString, expectedJsonString);
  });

  test('stripJsonComments.stripJsonComments() simple json with no whitespace', () => {
    const jsonString = `{"name":"John","age":30,"city":"New York"}`;
    const strippedJsonString = stripJsonComments(jsonString, { whitespace: false });
    const expectedJsonString = `{"name":"John","age":30,"city":"New York"}`;

    assert.strictEqual(strippedJsonString, expectedJsonString);
  });

  test('stripJsonComments.stripJsonComments() jsonString is not a json', () => {
    const jsonString = '123';
    const strippedJsonString = stripJsonComments(jsonString, { whitespace: false });
    const expectedJsonString = `123`;

    assert.strictEqual(strippedJsonString, expectedJsonString);
  });

  test('handles escaped quotes correctly', () => {
    const jsonString = '{"key": "value with \\"escaped\\" quotes"}';
    const strippedJsonString = stripJsonComments(jsonString, { whitespace: false });
    const expected = '{"key": "value with \\"escaped\\" quotes"}';
    assert.strictEqual(strippedJsonString, expected);
  });

  test('stripJsonComments.stripJsonComments() with single-line comment ending with \\r\\n', () => {
    const jsonString = '{\n  "key": "value", // comment\r\n  "key2": "value2"\n}';
    const expectedJsonString = { key: 'value', key2: 'value2' };
    const strippedJsonString = JSON.parse(stripJsonComments(jsonString));
    assert.deepStrictEqual(strippedJsonString, expectedJsonString);
  });

  test('stripJsonComments.stripJsonComments() with unclosed comment at the end', () => {
    const jsonString = '{\n  "key": "value",\n  "key2": "value2" /* This is an unclosed comment */}';
    const expectedJsonString = { key: 'value', key2: 'value2' };
    const strippedJsonString = JSON.parse(stripJsonComments(jsonString));
    assert.deepStrictEqual(strippedJsonString, expectedJsonString);
  });

  test('replace comments with whitespace', () => {
    assert.strictEqual(stripJsonComments('//comment\n{"a":"b"}'), '         \n{"a":"b"}');
    assert.strictEqual(stripJsonComments('/*//comment*/{"a":"b"}'), '             {"a":"b"}');
    assert.strictEqual(stripJsonComments('{"a":"b"//comment\n}'), '{"a":"b"         \n}');
    assert.strictEqual(stripJsonComments('{"a":"b"/*comment*/}'), '{"a":"b"           }');
    assert.strictEqual(stripJsonComments('{"a"/*\n\n\ncomment\r\n*/:"b"}'), '{"a"  \n\n\n       \r\n  :"b"}');
    assert.strictEqual(stripJsonComments('/*!\n * comment\n */\n{"a":"b"}'), '   \n          \n   \n{"a":"b"}');
    assert.strictEqual(stripJsonComments('{/*comment*/"a":"b"}'), '{           "a":"b"}');
  });

  test('remove comments', () => {
    const options = { whitespace: false };
    assert.strictEqual(stripJsonComments('//comment\n{"a":"b"}', options), '\n{"a":"b"}');
    assert.strictEqual(stripJsonComments('/*//comment*/{"a":"b"}', options), '{"a":"b"}');
    assert.strictEqual(stripJsonComments('{"a":"b"//comment\n}', options), '{"a":"b"\n}');
    assert.strictEqual(stripJsonComments('{"a":"b"/*comment*/}', options), '{"a":"b"}');
    assert.strictEqual(stripJsonComments('{"a"/*\n\n\ncomment\r\n*/:"b"}', options), '{"a":"b"}');
    assert.strictEqual(stripJsonComments('/*!\n * comment\n */\n{"a":"b"}', options), '\n{"a":"b"}');
    assert.strictEqual(stripJsonComments('{/*comment*/"a":"b"}', options), '{"a":"b"}');
  });

  test("doesn't strip comments inside strings", () => {
    assert.strictEqual(stripJsonComments('{"a":"b//c"}'), '{"a":"b//c"}');
    assert.strictEqual(stripJsonComments('{"a":"b/*c*/"}'), '{"a":"b/*c*/"}');
    assert.strictEqual(stripJsonComments('{"/*a":"b"}'), '{"/*a":"b"}');
    assert.strictEqual(stripJsonComments('{"\\"/*a":"b"}'), '{"\\"/*a":"b"}');
  });

  test('consider escaped slashes when checking for escaped string quote', () => {
    assert.strictEqual(stripJsonComments('{"\\\\":"https://foobar.com"}'), '{"\\\\":"https://foobar.com"}');
    assert.strictEqual(stripJsonComments('{"foo\\"":"https://foobar.com"}'), '{"foo\\"":"https://foobar.com"}');
  });

  test('line endings - no comments', () => {
    assert.strictEqual(stripJsonComments('{"a":"b"\n}'), '{"a":"b"\n}');
    assert.strictEqual(stripJsonComments('{"a":"b"\r\n}'), '{"a":"b"\r\n}');
  });

  test('line endings - single line comment', () => {
    assert.strictEqual(stripJsonComments('{"a":"b"//c\n}'), '{"a":"b"   \n}');
    assert.strictEqual(stripJsonComments('{"a":"b"//c\r\n}'), '{"a":"b"   \r\n}');
  });

  test('line endings - single line block comment', () => {
    assert.strictEqual(stripJsonComments('{"a":"b"/*c*/\n}'), '{"a":"b"     \n}');
    assert.strictEqual(stripJsonComments('{"a":"b"/*c*/\r\n}'), '{"a":"b"     \r\n}');
  });

  test('line endings - multi line block comment', () => {
    assert.strictEqual(stripJsonComments('{"a":"b",/*c\nc2*/"x":"y"\n}'), '{"a":"b",   \n    "x":"y"\n}');
    assert.strictEqual(stripJsonComments('{"a":"b",/*c\r\nc2*/"x":"y"\r\n}'), '{"a":"b",   \r\n    "x":"y"\r\n}');
  });

  test('line endings - works at EOF', () => {
    const options = { whitespace: false };
    assert.strictEqual(stripJsonComments('{\r\n\t"a":"b"\r\n} //EOF'), '{\r\n\t"a":"b"\r\n}      ');
    assert.strictEqual(stripJsonComments('{\r\n\t"a":"b"\r\n} //EOF', options), '{\r\n\t"a":"b"\r\n} ');
  });

  test('handles weird escaping', () => {
    assert.strictEqual(
      stripJsonComments(String.raw`{"x":"x \"sed -e \\\"s/^.\\\\{46\\\\}T//\\\" -e \\\"s/#033/\\\\x1b/g\\\"\""}`),
      String.raw`{"x":"x \"sed -e \\\"s/^.\\\\{46\\\\}T//\\\" -e \\\"s/#033/\\\\x1b/g\\\"\""}`,
    );
  });

  test('strips trailing commas', () => {
    assert.strictEqual(stripJsonComments('{"x":true,}', { trailingCommas: true }), '{"x":true }');
    assert.strictEqual(stripJsonComments('{"x":true,}', { trailingCommas: true, whitespace: false }), '{"x":true}');
    assert.strictEqual(stripJsonComments('{"x":true,\n  }', { trailingCommas: true }), '{"x":true \n  }');
    assert.strictEqual(stripJsonComments('[true, false,]', { trailingCommas: true }), '[true, false ]');
    assert.strictEqual(
      stripJsonComments('[true, false,]', { trailingCommas: true, whitespace: false }),
      '[true, false]',
    );
    assert.strictEqual(
      stripJsonComments('{\n  "array": [\n    true,\n    false,\n  ],\n}', { trailingCommas: true, whitespace: false }),
      '{\n  "array": [\n    true,\n    false\n  ]\n}',
    );
    assert.strictEqual(
      stripJsonComments('{\n  "array": [\n    true,\n    false /* comment */ ,\n /*comment*/ ],\n}', {
        trailingCommas: true,
        whitespace: false,
      }),
      '{\n  "array": [\n    true,\n    false  \n  ]\n}',
    );
  });
});
