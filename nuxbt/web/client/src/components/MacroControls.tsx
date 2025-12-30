import { useState, useEffect, useRef } from 'react';
import { Play, Square, Save, Trash2, Keyboard, Circle, ChevronDown, Plus } from 'lucide-react';
import { socket } from '../socket';
import type { DirectInputPacket, ControllerState } from '../types';

interface Props {
  controllerIndex: string;
  input: DirectInputPacket;
  controllerState: ControllerState;
}

interface MacroStep {
  packet: DirectInputPacket;
  duration: number;
}

export function MacroControls({ controllerIndex, input, controllerState }: Props) {
  const [macroText, setMacroText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  
  // Loop State
  const [loopCount, setLoopCount] = useState(0);
  const [isInfinite, setIsInfinite] = useState(false);
  
  // Macro Data State
  const [categories, setCategories] = useState<Record<string, string[]>>({});
  const [selectedCategory, setSelectedCategory] = useState<string>('Uncategorized');
  const [selectedMacro, setSelectedMacro] = useState<string>(''); // Empty string = New Macro
  
  // Name Editing
  const [currentMacroName, setCurrentMacroName] = useState<string>('');
  
  // New Category Modal
  const [showNewCategoryModal, setShowNewCategoryModal] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');

  // Execution State
  const [runningMacroId, setRunningMacroId] = useState<string | null>(null);
  const loopsRemaining = useRef(0);

  // Recording State
  const recordedMacro = useRef<MacroStep[]>([]);
  const recordingStartTime = useRef<number>(0);
  const lastInputPacket = useRef<DirectInputPacket | null>(null);

  useEffect(() => {
    fetchMacros();
  }, []);

  // Loop Monitor
  useEffect(() => {
    if (runningMacroId && controllerState.finished_macros && controllerState.finished_macros.includes(runningMacroId)) {
        if (isInfinite || loopsRemaining.current > 0) {
            if (!isInfinite) loopsRemaining.current -= 1;
            setTimeout(() => {
                emitMacro(); 
            }, 50);
        } else {
            setRunningMacroId(null);
        }
    }
  }, [controllerState.finished_macros, runningMacroId, isInfinite]);

  // Recording Monitor
  useEffect(() => {
    if (!isRecording) return;
    const currentInputStr = JSON.stringify(input);
    const lastInputStr = lastInputPacket.current ? JSON.stringify(lastInputPacket.current) : '';

    if (!lastInputPacket.current) {
        lastInputPacket.current = JSON.parse(currentInputStr);
        return;
    }

    if (currentInputStr !== lastInputStr) {
        const now = performance.now();
        let duration = (now - recordingStartTime.current) / 1000;
        if (duration < 0) duration = 0;
        recordedMacro.current.push({
            packet: lastInputPacket.current as DirectInputPacket,
            duration: duration
        });
        recordingStartTime.current = now;
        lastInputPacket.current = JSON.parse(currentInputStr);
    }
  }, [input, isRecording]);

  const fetchMacros = async () => {
    try {
      const res = await fetch('/api/macros');
      const data = await res.json();
      // Ensure Uncategorized exists in data if empty, or at least handle it
      if (!data["Uncategorized"]) {
          data["Uncategorized"] = [];
      }
      setCategories(data);
      return data;
    } catch (e) {
      console.error('Failed to fetch macros', e);
      return null;
    }
  };

  const handleRecord = () => {
    if (!isRecording) {
        setIsRecording(true);
        recordedMacro.current = [];
        recordingStartTime.current = performance.now();
        lastInputPacket.current = null;
        setMacroText('');
    } else {
        setIsRecording(false);
        const now = performance.now();
        let duration = (now - recordingStartTime.current) / 1000;
        if (duration < 0) duration = 0;
        if (lastInputPacket.current) {
            recordedMacro.current.push({
                packet: lastInputPacket.current,
                duration: duration
            });
        }
        setMacroText(generateMacroString(recordedMacro.current));
    }
  };

  const generateMacroString = (steps: MacroStep[]) => {
      const lines: string[] = [];
      const pad3 = (num: number) => {
          let s = Math.abs(Math.round(num)).toString();
          while (s.length < 3) s = "0" + s;
          return s;
      };
      
      const formatStick = (name: string, x: number, y: number) => {
          const xFmt = (x >= 0 ? "+" : "-") + pad3(x);
          const yFmt = (y >= 0 ? "+" : "-") + pad3(y);
          return `${name}@${xFmt}${yFmt}`;
      };

      for (const step of steps) {
          const p = step.packet;
          const d = step.duration.toFixed(3) + "s";
          const buttons: string[] = [];

          if (p.A) buttons.push("A");
          if (p.B) buttons.push("B");
          if (p.X) buttons.push("X");
          if (p.Y) buttons.push("Y");
          if (p.PLUS) buttons.push("PLUS");
          if (p.MINUS) buttons.push("MINUS");
          if (p.HOME) buttons.push("HOME");
          if (p.CAPTURE) buttons.push("CAPTURE");
          if (p.L) buttons.push("L");
          if (p.R) buttons.push("R");
          if (p.ZL) buttons.push("ZL");
          if (p.ZR) buttons.push("ZR");
          if (p.DPAD_UP) buttons.push("DPAD_UP");
          if (p.DPAD_DOWN) buttons.push("DPAD_DOWN");
          if (p.DPAD_LEFT) buttons.push("DPAD_LEFT");
          if (p.DPAD_RIGHT) buttons.push("DPAD_RIGHT");
          if (p.L_STICK.PRESSED) buttons.push("L_STICK_PRESS");
          if (p.R_STICK.PRESSED) buttons.push("R_STICK_PRESS");

          const ly = p.L_STICK.Y_VALUE;
          const lx = p.L_STICK.X_VALUE;
          if (Math.round(lx) !== 0 || Math.round(ly) !== 0) buttons.push(formatStick("L_STICK", lx, ly));
          const ry = p.R_STICK.Y_VALUE;
          const rx = p.R_STICK.X_VALUE;
          if (Math.round(rx) !== 0 || Math.round(ry) !== 0) buttons.push(formatStick("R_STICK", rx, ry));

          const line = buttons.join(" ");
          lines.push(line ? `${line} ${d}` : d);
      }
      return lines.join("\n");
  };

  const emitMacro = () => {
      if (!macroText.trim()) return;
      socket.emit('macro', JSON.stringify([parseInt(controllerIndex), macroText.toUpperCase()]), (response: string) => {
          setRunningMacroId(response);
      });
  };

  const startSequence = () => {
      loopsRemaining.current = loopCount; 
      emitMacro();
  };

  const stopAll = () => {
      setRunningMacroId(null);
      loopsRemaining.current = 0;
      socket.emit('stop_all_macros');
  };

  const saveMacro = async () => {
      if (!currentMacroName.trim() || !macroText) return;
      await fetch('/api/macros', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ 
              name: currentMacroName, 
              category: selectedCategory,
              macro: macroText 
          })
      });
      await fetchMacros();
      // If we saved a new name, select it
      setSelectedMacro(currentMacroName);
  };
  
  const loadMacroContent = async (category: string, name: string) => {
      if (!name) {
          setMacroText('');
          setCurrentMacroName('');
          return;
      }
      try {
          const res = await fetch(`/api/macros/${encodeURIComponent(category)}/${encodeURIComponent(name)}`);
          if (res.ok) {
              const data = await res.json();
              setMacroText(data.macro);
              setCurrentMacroName(name);
          }
      } catch (e) {
          console.error("Failed to load macro", e);
      }
  };

  // Delete Modal State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [keepCategory, setKeepCategory] = useState(false);

  const handleDeleteClick = () => {
      if (!selectedMacro) return;
      setShowDeleteModal(true);
      setKeepCategory(false);
  };

  const confirmDelete = async () => {
      if (!selectedMacro) return;
      
      await fetch(`/api/macros/${encodeURIComponent(selectedCategory)}/${encodeURIComponent(selectedMacro)}`, { method: 'DELETE' });
      const newCategories = await fetchMacros();
      
      const categoryWasEmpty = newCategories && !newCategories[selectedCategory];
      
      if (categoryWasEmpty) {
          if (keepCategory) {
              // Restore it as an empty category (like a new one)
              setCategories(prev => ({
                  ...prev,
                  [selectedCategory]: []
              }));
              // Stay on this category
          } else {
              // Fallback to Uncategorized
              setSelectedCategory('Uncategorized');
          }
      }
      
      setShowDeleteModal(false);
      setSelectedMacro('');
      setMacroText('');
      setCurrentMacroName('');
  };

  // Handle Category Change
  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      const val = e.target.value;
      if (val === '__NEW__') {
          setShowNewCategoryModal(true);
      } else {
          setSelectedCategory(val);
          setSelectedMacro('');
          // Do NOT clear text/name
      }
  };

  // Handle Macro Selection Change
  const handleMacroChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      const val = e.target.value;
      setSelectedMacro(val);
      // Do NOT auto-load
  };

  const handleLoad = () => {
      if (selectedMacro) {
          loadMacroContent(selectedCategory, selectedMacro);
      }
  };
  
  const createCategory = () => {
      if (newCategoryName.trim()) {
          // Temporarily add to list, will be persisted when a macro is saved to it
          setCategories(prev => ({
              ...prev,
              [newCategoryName.trim()]: []
          }));
          setSelectedCategory(newCategoryName.trim());
          setSelectedMacro('');
          // Do NOT clear text/name
      }
      setShowNewCategoryModal(false);
      setNewCategoryName('');
  };

  // Keybind State
  const [recordKey, setRecordKey] = useState<string>('KeyR');
  const [recordBtn, setRecordBtn] = useState<number | null>(null);

  useEffect(() => {
     fetch('/api/keybinds')
        .then(r => r.json())
        .then(d => {
            if(d && d.keyboard && d.keyboard['RECORD_MACRO']) {
                setRecordKey(d.keyboard['RECORD_MACRO']);
            }
            if(d && d.gamepad && d.gamepad.buttons && d.gamepad.buttons['RECORD_MACRO'] !== undefined) {
                setRecordBtn(d.gamepad.buttons['RECORD_MACRO']);
            }
        })
        .catch(() => {});
  }, []);

  // Record Keybind Listener (Keyboard)
  useEffect(() => {
      const handleKeyUp = (e: KeyboardEvent) => {
          if (e.code === recordKey) {
              const tag = (e.target as HTMLElement).tagName;
              if (tag === 'INPUT' || tag === 'TEXTAREA') return;
              handleRecord();
          }
      };
      window.addEventListener('keyup', handleKeyUp);
      return () => window.removeEventListener('keyup', handleKeyUp);
  }, [handleRecord, recordKey]);

  // Record Gamepad Listener
  const recordBtnPressed = useRef(false);
  useEffect(() => {
      if (recordBtn === null) return;
      
      let frameId: number;

      const loop = () => {
          const gps = navigator.getGamepads ? navigator.getGamepads() : [];
          const gp = gps[0];
          if (gp && gp.buttons[recordBtn]) {
              const pressed = gp.buttons[recordBtn].pressed;
              if (pressed && !recordBtnPressed.current) {
                  handleRecord();
              }
              recordBtnPressed.current = pressed;
          }
          frameId = requestAnimationFrame(loop);
      };
      
      frameId = requestAnimationFrame(loop);
      return () => cancelAnimationFrame(frameId);
  }, [handleRecord, recordBtn]);

  const isRunning = runningMacroId !== null;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-3xl overflow-hidden shadow-lg border border-slate-100 dark:border-slate-700 flex flex-col h-[600px] xl:h-[700px]">
      <div className="p-4 border-b border-slate-100 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50 flex flex-col gap-3">
        <label className="text-xs font-bold uppercase text-slate-400 tracking-wider">Macro Name</label>
        <div className="flex items-center gap-2">
            <Keyboard size={20} className="text-honey-500" />
            <input 
                type="text" 
                value={currentMacroName}
                onChange={(e) => setCurrentMacroName(e.target.value)}
                placeholder="New Macro"
                className="bg-transparent text-lg font-bold text-slate-800 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none w-full"
            />
        </div>
      </div>

      {/* Editor Area */}
      <div className="flex-1 p-0 relative group">
        <textarea
          value={macroText}
          onChange={(e) => setMacroText(e.target.value)}
          disabled={isRecording || isRunning}
          placeholder={isRecording ? "Recording inputs..." : "Type or record your macro here...\nFormat: <Buttons> <Duration>\nExample: A B 0.5s"}
          className="w-full h-full p-4 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono text-sm resize-none focus:outline-none focus:bg-slate-50 dark:focus:bg-slate-900/50 transition-colors"
        />
        {(isRecording || isRunning) && (
            <div className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/5 backdrop-blur-md border border-white/10 text-xs font-bold uppercase tracking-wider">
                {isRecording && <span className="flex items-center gap-1 text-rose-500 animate-pulse"><Circle size={8} fill="currentColor" /> REC</span>}
                {isRunning && <span className="flex items-center gap-1 text-emerald-500"><Play size={8} fill="currentColor" /> RUNNING</span>}
            </div>
        )}
      </div>

      {/* Control Panel */}
      <div className="bg-slate-100 dark:bg-[#1e1e30] p-4 border-t border-slate-200 dark:border-slate-700 space-y-4">
        
        {/* Selection Row */}
        <div className="flex flex-col gap-3">
            <div className="relative">
                <select 
                    value={selectedCategory}
                    onChange={handleCategoryChange}
                    className="w-full appearance-none px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-700 dark:text-slate-200 font-medium focus:outline-none focus:ring-2 focus:ring-honey-400"
                >
                    {Object.keys(categories).sort().map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                    ))}
                    <option value="__NEW__">+ New Category...</option>
                </select>
                <ChevronDown size={14} className="absolute right-3 top-3.5 text-slate-400 pointer-events-none" />
            </div>
            
            <div className="flex gap-2">
                <div className="relative flex-1">
                    <select 
                        value={selectedMacro}
                        onChange={handleMacroChange}
                        className="w-full appearance-none px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-700 dark:text-slate-200 font-medium focus:outline-none focus:ring-2 focus:ring-honey-400"
                    >
                        <option value="">(New Macro)</option>
                        {categories[selectedCategory]?.map(m => (
                            <option key={m} value={m}>{m}</option>
                        ))}
                    </select>
                    <ChevronDown size={14} className="absolute right-3 top-3.5 text-slate-400 pointer-events-none" />
                </div>
                <button
                    onClick={handleLoad}
                    disabled={!selectedMacro}
                    className="px-3 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl font-bold text-xs disabled:opacity-50 hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
                >
                    Load
                </button>
            </div>
        </div>

        {/* Loop Section */}
        <div className="flex items-center justify-between bg-white dark:bg-slate-800 p-3 rounded-xl border border-slate-200 dark:border-slate-600 shadow-sm">
             {/* ... Loop controls same as before ... */}
             <div className="flex items-center gap-3">
                 <span className="text-sm font-bold text-slate-700 dark:text-slate-300">Loop</span>
                 <div className="flex items-center bg-slate-100 dark:bg-slate-700 rounded-lg p-0.5">
                    <button 
                        onClick={() => setLoopCount(Math.max(0, loopCount - 1))}
                        disabled={isInfinite || loopCount <= 0}
                        className="p-1.5 hover:bg-white dark:hover:bg-slate-600 text-slate-500 rounded-md disabled:opacity-30 transition-shadow"
                    >
                        <Plus className="rotate-45" size={14} /> 
                    </button>
                    <div className="w-10 text-center text-sm font-mono font-bold text-slate-700 dark:text-slate-200">
                        {loopCount}
                    </div>
                    <button 
                        onClick={() => setLoopCount(loopCount + 1)}
                        disabled={isInfinite}
                        className="p-1.5 hover:bg-white dark:hover:bg-slate-600 text-slate-500 rounded-md disabled:opacity-30 transition-shadow"
                    >
                        <Plus size={14} />
                    </button>
                 </div>
             </div>

            <label className="flex items-center gap-2 cursor-pointer select-none group">
                <div className={`w-5 h-5 rounded border flex items-center justify-center transition-all ${isInfinite ? 'bg-honey-500 border-honey-500' : 'bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-500 group-hover:border-honey-400'}`}>
                    {isInfinite && <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="4"><polyline points="20 6 9 17 4 12" /></svg>}
                </div>
                <input 
                    type="checkbox" 
                    className="hidden"
                    checked={isInfinite}
                    onChange={(e) => setIsInfinite(e.target.checked)}
                />
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400 group-hover:text-slate-800 dark:group-hover:text-slate-200">Until Stopped</span>
            </label>
        </div>

        {/* Action Grid (2x2) */}
        <div className="grid grid-cols-2 gap-3">
             {/* Delete (if loaded) or Placeholder */}
             {selectedMacro ? (
                 <button 
                    onClick={handleDeleteClick}
                    className="flex items-center justify-center gap-2 px-4 py-3 bg-rose-50 dark:bg-rose-900/20 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800 hover:bg-rose-100 dark:hover:bg-rose-900/40 rounded-xl font-bold transition-all shadow-sm active:scale-[0.98]"
                >
                    <Trash2 size={18} />
                    Delete
                </button>
             ) : (
                <div /> // Spacer
             )}


             {/* Save */}
            <button 
                onClick={saveMacro}
                disabled={!macroText.trim() || !currentMacroName.trim()}
                className="flex items-center justify-center gap-2 px-4 py-3 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 hover:border-slate-300 dark:hover:border-slate-500 rounded-xl font-bold transition-all shadow-sm active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100"
            >
                <Save size={18} />
                Save
            </button>

            {/* Record */}
            <button 
                onClick={handleRecord}
                disabled={isRunning}
                className={`flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-bold transition-all shadow-sm active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 border ${
                    isRecording 
                    ? 'bg-rose-50 text-rose-600 border-rose-200 dark:bg-rose-900/20 dark:border-rose-800 animate-pulse' 
                    : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 hover:border-slate-300 dark:hover:border-slate-500'
                }`}
            >
                <div className={`w-2.5 h-2.5 rounded-full ${isRecording ? 'bg-rose-500' : 'bg-rose-500'}`} />
                {isRecording ? 'Stop Rec' : 'Record'}
            </button>

            {/* Run / Stop */}
            <button 
                onClick={isRunning ? stopAll : startSequence}
                disabled={isRecording}
                className={`flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-bold transition-all shadow-md active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 text-white ${
                    isRunning 
                    ? 'bg-rose-500 hover:bg-rose-600 shadow-rose-500/20' 
                    : 'bg-emerald-500 hover:bg-emerald-600 shadow-emerald-500/20'
                }`}
            >
                {isRunning ? (
                    <>
                        <Square size={18} fill="currentColor" />
                        Stop
                    </>
                ) : (
                    <>
                        <Play size={18} fill="currentColor" />
                        Run
                    </>
                )}
            </button>
        </div>

      </div>

        {/* Delete Confirmation Modal */}
        {showDeleteModal && (
            <div className="absolute inset-0 z-50 rounded-3xl bg-black/10 backdrop-blur-[2px] flex items-center justify-center p-4">
                 <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-600 p-6 w-full max-w-sm animate-in zoom-in-95 duration-200">
                     <h4 className="font-bold text-xl dark:text-slate-100 mb-2">Delete Macro?</h4>
                     <p className="text-slate-600 dark:text-slate-400 mb-4">
                         Do you want to delete macro: <span className="font-bold text-slate-800 dark:text-slate-200">{selectedMacro}</span>?
                     </p>
                     
                     {selectedCategory !== 'Uncategorized' && categories[selectedCategory]?.length === 1 && (
                         <div className="mb-6 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-100 dark:border-amber-800/50">
                             <p className="text-sm text-amber-700 dark:text-amber-400 mb-2">
                                 This will also remove the <span className="font-bold">{selectedCategory}</span> category.
                             </p>
                             <label className="flex items-center gap-2 cursor-pointer">
                                <input 
                                    type="checkbox" 
                                    checked={keepCategory}
                                    onChange={(e) => setKeepCategory(e.target.checked)}
                                    className="rounded border-slate-300 text-honey-500 focus:ring-honey-400"
                                />
                                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Keep Category</span>
                             </label>
                         </div>
                     )}
                     
                     <div className="flex justify-end gap-3">
                         <button 
                            onClick={() => setShowDeleteModal(false)}
                            className="px-5 py-2.5 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl font-bold transition-colors"
                        >
                            Cancel
                        </button>
                        <button 
                            onClick={confirmDelete}
                            className="px-5 py-2.5 bg-rose-500 hover:bg-rose-600 text-white rounded-xl font-bold transition-all shadow-lg shadow-rose-500/20"
                        >
                            Delete
                        </button>
                     </div>
                 </div>
            </div>
        )}

        {/* New Category Modal */}
        {showNewCategoryModal && (
            <div className="absolute inset-0 z-50 rounded-3xl bg-black/10 backdrop-blur-[2px] flex items-center justify-center p-4">
                 <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-600 p-6 w-full max-w-sm animate-in zoom-in-95 duration-200">
                     <h4 className="font-bold text-xl dark:text-slate-100 mb-4">New Category</h4>
                     
                     <div className="mb-6">
                         <input 
                            type="text" 
                            value={newCategoryName}
                            onChange={(e) => setNewCategoryName(e.target.value)}
                            placeholder="Category Name"
                            autoFocus
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-base focus:ring-2 focus:ring-honey-400 focus:outline-none dark:text-slate-100"
                        />
                     </div>
                     
                     <div className="flex justify-end gap-3">
                         <button 
                            onClick={() => {
                                setShowNewCategoryModal(false);
                                setNewCategoryName('');
                                // Reset to default if cancelled
                                setSelectedCategory('Uncategorized');
                            }}
                            className="px-5 py-2.5 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl font-bold transition-colors"
                        >
                            Cancel
                        </button>
                        <button 
                            onClick={createCategory}
                            disabled={!newCategoryName.trim()}
                            className="px-5 py-2.5 bg-honey-400 hover:bg-honey-500 text-white rounded-xl font-bold transition-all shadow-lg shadow-honey-400/20 disabled:opacity-50 disabled:shadow-none"
                        >
                            Create
                        </button>
                     </div>
                 </div>
            </div>
        )}
    </div>
  );
}
