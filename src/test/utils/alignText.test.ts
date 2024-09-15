import * as assert from 'assert';
import alignText, { formatLabel } from '../../utils/alignText';

suite('alignText Test Suite', () => {
  test('formatLabel', () => {
    const a = formatLabel('$(star-full) By Rating | You can find most interesting themes here');
    assert.strictEqual(a.length, 80);
  });

  test('alignText', () => {
    const labels = [
      {
        label: '$(star-full) By Rating | You can find most interesting themes here',
        description: '12.4K themes',
        theme_list_file: 'byrating',
      },
      {
        label: '$(arrow-up) Trending Weekly | A bit more interesting than most installed',
        description: '',
        theme_list_file: 'trendingweekly',
      },
    ];
    const alignedLabels = alignText(labels);
    assert.strictEqual(alignedLabels[0].label.length, 80);
    assert.strictEqual(alignedLabels[1].label.length, 79);
  });
});
