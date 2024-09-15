function formatLabel(label: string) {
  // Extract the $(...) section
  const iconMatch = label.match(/^\$\([^)]+\)/);
  const icon = iconMatch ? iconMatch[0] : ''; // Add a space after the icon

  // Extract the text after the icon
  const text = label.replace(icon, '').trim();
  const parts = text.split(' | ').map((part) => part.trim());
  const totalTextLength = parts.reduce((sum, part) => sum + part.length, 0);
  const totalSpace = 67 - totalTextLength;
  const spaceBetweenParts = Math.floor(totalSpace / (parts.length - 1));
  const extraSpace = totalSpace % (parts.length - 1);

  return `${icon} ${parts.join(`${' '.repeat(spaceBetweenParts)}${extraSpace > 0 ? ' ' : ''}`)}`;
}

export default function alignText(labels: any[]) {
  const newLabels = labels.map((obj) => {
    obj.label = formatLabel(obj.label);
    return obj;
  });
  return newLabels;
}
