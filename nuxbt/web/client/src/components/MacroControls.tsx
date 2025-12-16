import { useState, useEffect, useRef } from 'react';
import { Play, Square, Save, FolderOpen, Trash2, Keyboard, X, Plus, Minus, Circle } from 'lucide-react';
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
  
  // Macro Handling State
  const [macroName, setMacroName] = useState('');
  const [savedMacros, setSavedMacros] = useState<string[]>([]);
  
  // Modals
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showLoadModal, setShowLoadModal] = useState(false);
  
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
      setSavedMacros(data);
    } catch (e) {
      console.error('Failed to fetch macros', e);
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
      if (!macroName || !macroText) return;
      await fetch('/api/macros', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ name: macroName, macro: macroText })
      });
      fetchMacros();
      setShowSaveModal(false);
      setMacroName('');
  };
  
  const loadMacro = async (name: string) => {
      const res = await fetch(`/api/macros/${encodeURIComponent(name)}`);
      if (res.ok) {
          const data = await res.json();
          setMacroText(data.macro);
      }
      setShowLoadModal(false);
  };
  
  const deleteMacro = async (name: string, e: React.MouseEvent) => {
     e.stopPropagation();
     if (!confirm(`Delete ${name}?`)) return;
      await fetch(`/api/macros/${encodeURIComponent(name)}`, { method: 'DELETE' });
      setSavedMacros(prev => prev.filter(m => m !== name));
  };

  // R Keybind
  useEffect(() => {
      const handleKeyUp = (e: KeyboardEvent) => {
          if (e.key.toLowerCase() === 'r') {
              const tag = (e.target as HTMLElement).tagName;
              if (tag === 'INPUT' || tag === 'TEXTAREA') return;
              handleRecord();
          }
      };
      window.addEventListener('keyup', handleKeyUp);
      return () => window.removeEventListener('keyup', handleKeyUp);
  }, [handleRecord]);

  const isRunning = runningMacroId !== null;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-3xl overflow-hidden shadow-lg border border-slate-100 dark:border-slate-700 flex flex-col h-[600px] xl:h-[700px]">
      <div className="p-4 border-b border-slate-100 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50">
        <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <Keyboard size={20} className="text-honey-500" />
            Macro Editor
        </h3>
      </div>

      {/* Editor Area (Maximizes space) */}
      <div className="flex-1 p-0 relative group">
        <textarea
          value={macroText}
          onChange={(e) => setMacroText(e.target.value)}
          disabled={isRecording || isRunning}
          placeholder={isRecording ? "Recording inputs..." : "Type or record your macro here...\nFormat: <Buttons> <Duration>\nExample: A B 0.5s"}
          className="w-full h-full p-4 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono text-sm resize-none focus:outline-none focus:bg-slate-50 dark:focus:bg-slate-900/50 transition-colors"
        />
        {/* Status Overlay */}
        {(isRecording || isRunning) && (
            <div className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/5 backdrop-blur-md border border-white/10 text-xs font-bold uppercase tracking-wider">
                {isRecording && <span className="flex items-center gap-1 text-rose-500 animate-pulse"><Circle size={8} fill="currentColor" /> REC</span>}
                {isRunning && <span className="flex items-center gap-1 text-emerald-500"><Play size={8} fill="currentColor" /> RUNNING</span>}
            </div>
        )}
      </div>

      {/* Control Panel (Darker Background) */}
      <div className="bg-slate-100 dark:bg-[#1e1e30] p-4 border-t border-slate-200 dark:border-slate-700 space-y-4">
        
        {/* Loop Section */}
        <div className="flex items-center justify-between bg-white dark:bg-slate-800 p-3 rounded-xl border border-slate-200 dark:border-slate-600 shadow-sm">
             <div className="flex items-center gap-3">
                 <span className="text-sm font-bold text-slate-700 dark:text-slate-300">Loop</span>
                 <div className="flex items-center bg-slate-100 dark:bg-slate-700 rounded-lg p-0.5">
                    <button 
                        onClick={() => setLoopCount(Math.max(0, loopCount - 1))}
                        disabled={isInfinite || loopCount <= 0}
                        className="p-1.5 hover:bg-white dark:hover:bg-slate-600 text-slate-500 rounded-md disabled:opacity-30 transition-shadow"
                    >
                        <Minus size={14} />
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
             {/* Load */}
            <button 
                onClick={() => setShowLoadModal(true)}
                className="flex items-center justify-center gap-2 px-4 py-3 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 hover:border-slate-300 dark:hover:border-slate-500 rounded-xl font-bold transition-all shadow-sm active:scale-[0.98]"
            >
                <FolderOpen size={18} />
                Load
            </button>

             {/* Save */}
            <button 
                onClick={() => setShowSaveModal(true)}
                disabled={!macroText.trim()}
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
                    : 'bg-emerald-500 hover:bg-emerald-600 shadow-emerald-500/20' // Changed to Emerald for better distinction? Or Honey? User didn't specify color. Emerald is standard for Run.
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

        {/* Save Modal */}
        {showSaveModal && (
            <div className="absolute inset-0 z-50 rounded-3xl bg-black/10 backdrop-blur-[2px] flex items-center justify-center p-4">
                 <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-600 p-6 w-full max-w-sm animate-in zoom-in-95 duration-200">
                     <div className="flex justify-between items-center mb-6">
                         <h4 className="font-bold text-xl dark:text-slate-100">Save Macro</h4>
                         <button onClick={() => setShowSaveModal(false)} className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                             <X size={20} />
                         </button>
                     </div>
                     
                     <div className="mb-6">
                         <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Macro Name</label>
                         <input 
                            type="text" 
                            value={macroName}
                            onChange={(e) => setMacroName(e.target.value)}
                            placeholder="e.g. Speedrun Skip"
                            autoFocus
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-base focus:ring-2 focus:ring-honey-400 focus:outline-none dark:text-slate-100"
                        />
                     </div>
                     
                     <div className="flex justify-end gap-3">
                         <button 
                            onClick={() => setShowSaveModal(false)}
                            className="px-5 py-2.5 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl font-bold transition-colors"
                        >
                            Cancel
                        </button>
                        <button 
                            onClick={saveMacro}
                            disabled={!macroName.trim()}
                            className="px-5 py-2.5 bg-honey-400 hover:bg-honey-500 text-white rounded-xl font-bold transition-all shadow-lg shadow-honey-400/20 disabled:opacity-50 disabled:shadow-none"
                        >
                            Save Macro
                        </button>
                     </div>
                 </div>
            </div>
        )}
        
        {/* Load Modal */}
        {showLoadModal && (
            <div className="absolute inset-0 z-50 rounded-3xl bg-black/10 backdrop-blur-[2px] flex items-center justify-center p-4">
                 <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-600 p-6 w-full max-w-sm flex flex-col max-h-[85%] animate-in zoom-in-95 duration-200">
                     <div className="flex justify-between items-center mb-4">
                         <h4 className="font-bold text-xl dark:text-slate-100">Load Macro</h4>
                         <button onClick={() => setShowLoadModal(false)} className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                             <X size={20} />
                         </button>
                     </div>
                     
                     <div className="flex-1 overflow-y-auto -mx-2 px-2 space-y-2 mb-4">
                         {savedMacros.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-12 text-slate-400 gap-2">
                                <FolderOpen size={32} className="opacity-20" />
                                <p className="text-sm font-medium">No saved macros</p>
                            </div>
                         ) : (
                             savedMacros.map(m => (
                                 <div key={m} 
                                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-700/30 hover:bg-honey-50 dark:hover:bg-slate-700 border border-transparent hover:border-honey-200 dark:hover:border-slate-600 transition-all cursor-pointer group"
                                    onClick={() => loadMacro(m)}
                                 >
                                     <span className="font-semibold text-slate-700 dark:text-slate-200">{m}</span>
                                     <button 
                                        onClick={(e) => deleteMacro(m, e)}
                                        className="p-2 text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-900/20 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                        title="Delete"
                                     >
                                         <Trash2 size={16} />
                                     </button>
                                 </div>
                             ))
                         )}
                     </div>
                     
                     <div className="flex justify-end pt-4 border-t border-slate-100 dark:border-slate-700">
                         <button 
                            onClick={() => setShowLoadModal(false)}
                            className="px-5 py-2.5 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl font-bold transition-colors"
                        >
                            Cancel
                        </button>
                     </div>
                 </div>
            </div>
        )}
    </div>
  );
}
