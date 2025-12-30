import { useState, useEffect } from 'react';
import { Keyboard, Gamepad2, Save, RefreshCw } from 'lucide-react';
import type { KeyMap } from '../types';
import { DEFAULT_KEYBINDS, ACTIONS } from '../defaults';

export function KeyBindings() {
  const [activeSubTab, setActiveSubTab] = useState<'keyboard' | 'gamepad'>('keyboard');
  const [keyMap, setKeyMap] = useState<KeyMap>(DEFAULT_KEYBINDS);
  const [editingAction, setEditingAction] = useState<string | null>(null);
  const [listening, setListening] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    fetch('/api/keybinds')
      .then(res => res.json())
      .then(data => {
          if (data && data.keyboard) {
              setKeyMap(data);
          }
      })
      .catch(err => console.error(err));
  }, []);

  const save = async () => {
    try {
        await fetch('/api/keybinds', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(keyMap)
        });
        setHasChanges(false);
    } catch(e) {
        console.error("Failed to save", e);
    }
  };

  const reset = () => {
      setKeyMap(DEFAULT_KEYBINDS);
      setHasChanges(true);
  };

  // Keyboard Listener
  useEffect(() => {
      if (activeSubTab !== 'keyboard' || !listening || !editingAction) return;

      const handleDown = (e: KeyboardEvent) => {
          e.preventDefault();
          e.stopPropagation();
          
          setKeyMap(prev => ({
              ...prev,
              keyboard: {
                  ...prev.keyboard,
                  [editingAction]: e.code
              }
          }));
          setEditingAction(null);
          setListening(false);
          setHasChanges(true);
      };
      
      window.addEventListener('keydown', handleDown);
      return () => window.removeEventListener('keydown', handleDown);
  }, [activeSubTab, listening, editingAction]);

  // Gamepad Listener
  useEffect(() => {
      if (activeSubTab !== 'gamepad' || !listening || !editingAction) return;

      let frameId: number;
      const loop = () => {
          const gps = navigator.getGamepads ? navigator.getGamepads() : [];
          const gp = gps[0];
          if (gp) {
              // Check Buttons
              gp.buttons.forEach((btn, idx) => {
                  if (btn.pressed) {
                       setKeyMap(prev => ({
                          ...prev,
                          gamepad: {
                              ...prev.gamepad,
                              buttons: {
                                  ...prev.gamepad.buttons,
                                  [editingAction]: idx
                              },
                              axes: prev.gamepad.axes // Keep axes logic? Or remove existing mapping for this action?
                              // Ideally we should verify if we're mapping button or axis
                          }
                      }));
                      setEditingAction(null);
                      setListening(false);
                      setHasChanges(true);
                      return;
                  }
              });
              
              // Check Axes (Trigger threshold)
              // This is tricky because axes are always non-zero often. Use 0.5 threshold.
              gp.axes.forEach((val, idx) => {
                  if (Math.abs(val) > 0.7) {
                       setKeyMap(prev => ({
                          ...prev,
                          gamepad: {
                              ...prev.gamepad,
                              axes: {
                                  ...prev.gamepad.axes,
                                  [editingAction]: { index: idx, direction: val > 0 ? 1 : -1 }
                              }
                          }
                      }));
                      setEditingAction(null);
                      setListening(false);
                      setHasChanges(true);
                  }
              });
          }
          if (listening) frameId = requestAnimationFrame(loop);
      };
      
      frameId = requestAnimationFrame(loop);
      return () => cancelAnimationFrame(frameId);
  }, [activeSubTab, listening, editingAction]);


  const startEditing = (actionId: string) => {
      setEditingAction(actionId);
      setListening(true);
  };

  return (
    <div className="bg-white dark:bg-[#252540] rounded-2xl p-4 shadow-sm border border-slate-100 dark:border-slate-800 h-[600px] xl:h-[700px] flex flex-col">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-2">
          <div className="flex gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
              <button 
                onClick={() => setActiveSubTab('keyboard')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-bold text-xs transition-all ${activeSubTab === 'keyboard' ? 'bg-white dark:bg-slate-700 shadow text-slate-800 dark:text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'}`}
              >
                  <Keyboard size={16} />
                  Keyboard
              </button>
              <button 
                onClick={() => setActiveSubTab('gamepad')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-bold text-xs transition-all ${activeSubTab === 'gamepad' ? 'bg-white dark:bg-slate-700 shadow text-slate-800 dark:text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'}`}
              >
                  <Gamepad2 size={16} />
                  Gamepad
              </button>
          </div>
          
          <div className="flex gap-2">
               <button 
                  onClick={reset}
                  className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                  title="Reset Defaults"
               >
                   <RefreshCw size={18} />
               </button>
               <button 
                  onClick={save}
                  disabled={!hasChanges}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-honey-400 hover:bg-honey-500 disabled:opacity-50 disabled:bg-slate-200 dark:disabled:bg-slate-700 text-white rounded-lg font-bold text-xs transition-all shadow-sm"
               >
                   <Save size={16} />
                   Save Changes
               </button>
          </div>
      </div>

      <div className="flex-1 overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700 relative">
        <div className="absolute inset-0 overflow-y-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400 font-medium border-b border-slate-200 dark:border-slate-700 sticky top-0 backdrop-blur-sm">
            <tr>
              <th className="px-6 py-4">Action</th>
              <th className="px-6 py-4 text-right">Bound Input</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {ACTIONS.map((action) => {
                let bindLabel = "";
                const isEditing = editingAction === action.id;
                
                if (activeSubTab === 'keyboard') {
                    bindLabel = keyMap.keyboard[action.id] || "Unbound";
                } else {
                    // Gamepad Label
                    if (keyMap.gamepad.buttons[action.id] !== undefined) {
                        bindLabel = `Button ${keyMap.gamepad.buttons[action.id]}`;
                    } else if (keyMap.gamepad.axes[action.id] !== undefined) {
                        const ax = keyMap.gamepad.axes[action.id];
                        bindLabel = `Axis ${ax.index} ${ax.direction > 0 ? '+' : '-'}`;
                    } else {
                        bindLabel = "Unbound";
                    }
                }
                
                return (
                    <tr key={action.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors group">
                        <td className="px-6 py-3 font-medium text-slate-700 dark:text-slate-300">
                            {action.label}
                        </td>
                        <td className="px-6 py-3 text-right">
                            <button 
                                onClick={() => startEditing(action.id)}
                                disabled={listening}
                                className={`px-4 py-1.5 rounded-lg border font-mono text-xs transition-all min-w-[100px] ${
                                    isEditing 
                                    ? 'bg-honey-100 border-honey-300 text-honey-700 animate-pulse' 
                                    : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:border-honey-300 dark:hover:border-honey-500'
                                }`}
                            >
                                {isEditing ? "Listening..." : bindLabel}
                            </button>
                        </td>
                    </tr>
                );
            })}
          </tbody>
        </table>
      </div>
      </div>
      
      {activeSubTab === 'gamepad' && (
          <p className="mt-4 text-xs text-center text-slate-400">
              Note: Gamepad inputs require a connected controller. Try pressing buttons on your gamepad to map them.
          </p>
      )}
    </div>
  );
}
