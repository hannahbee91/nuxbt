export function KeyBindings() {
  const bindings = [
    { label: 'Left Stick', keys: 'W A S D' },
    { label: 'Left Stick Press', keys: 'T' },
    { label: 'Right Stick', keys: 'Arrow Keys' },
    { label: 'Right Stick Press', keys: 'Y' },
    { label: 'D-Pad', keys: 'G V B N' },
    { label: 'Home & Capture', keys: '[ & ]' },
    { label: 'Plus & Minus', keys: '6 & 7' },
    { label: 'A B X Y', keys: 'L K I J' },
    { label: 'L & ZL', keys: '1 & 2' },
    { label: 'R & ZR', keys: '8 & 9' },
    { label: 'Start/Stop Recording', keys: 'R' },
  ];

  return (
    <div className="bg-white dark:bg-[#252540] rounded-2xl p-6 shadow-sm border border-slate-100 dark:border-slate-800">
      <h3 className="text-lg font-semibold mb-4 text-slate-800 dark:text-slate-200">Keyboard Controls</h3>
      <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400 font-medium border-b border-slate-200 dark:border-slate-700">
            <tr>
              <th className="px-4 py-3">Control</th>
              <th className="px-4 py-3 text-right">Keys</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {bindings.map((item, i) => (
              <tr key={i} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors">
                <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{item.label}</td>
                <td className="px-4 py-3 text-right font-mono text-honey-600 dark:text-honey-400">{item.keys}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
