import React, { useState } from 'react';
import type { DirectInputPacket } from '../types';
import { socket } from '../socket';
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from 'lucide-react';

interface Props {
  index: string;
  initialInput: DirectInputPacket;
}

const EMPTY_PACKET: DirectInputPacket = {
  L_STICK: { PRESSED: false, X_VALUE: 0, Y_VALUE: 0 },
  R_STICK: { PRESSED: false, X_VALUE: 0, Y_VALUE: 0 },
  DPAD_UP: false, DPAD_DOWN: false, DPAD_LEFT: false, DPAD_RIGHT: false,
  L: false, ZL: false, R: false, ZR: false,
  JCL_SR: false, JCL_SL: false, JCR_SR: false, JCR_SL: false,
  PLUS: false, MINUS: false, HOME: false, CAPTURE: false,
  Y: false, X: false, B: false, A: false,
};

export const ControllerInput: React.FC<Props> = ({ index }) => {
  const [input, setInput] = useState<DirectInputPacket>(JSON.parse(JSON.stringify(EMPTY_PACKET)));

  const updateInput = (patch: Partial<DirectInputPacket>) => {
    const newInput = { ...input, ...patch };
    setInput(newInput);
    emitInput(newInput);
  };

  const emitInput = (packet: DirectInputPacket) => {
    socket.emit('input', JSON.stringify([parseInt(index), packet]));
  };

  // Keyboard input mapping
  React.useEffect(() => {
    const handleKey = (e: KeyboardEvent, pressed: boolean) => {
      // Ignore if user is typing in an input/textarea
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) {
        return;
      }

      const key = e.key.toUpperCase();
      const code = e.code;
      const updates: Partial<DirectInputPacket> = {};

      // Mapping based on old_index.html
      // Left Stick
      if (key === 'W') updates.L_STICK = { ...input.L_STICK, Y_VALUE: pressed ? 32767 : 0, PRESSED: input.L_STICK.PRESSED };
      if (key === 'S') updates.L_STICK = { ...input.L_STICK, Y_VALUE: pressed ? -32767 : 0, PRESSED: input.L_STICK.PRESSED };
      if (key === 'A') updates.L_STICK = { ...input.L_STICK, X_VALUE: pressed ? -32767 : 0, PRESSED: input.L_STICK.PRESSED };
      if (key === 'D') updates.L_STICK = { ...input.L_STICK, X_VALUE: pressed ? 32767 : 0, PRESSED: input.L_STICK.PRESSED };
      if (key === 'T') updates.L_STICK = { ...input.L_STICK, PRESSED: pressed };

      // Right Stick
      if (code === 'ArrowUp') updates.R_STICK = { ...input.R_STICK, Y_VALUE: pressed ? 32767 : 0, PRESSED: input.R_STICK.PRESSED };
      if (code === 'ArrowDown') updates.R_STICK = { ...input.R_STICK, Y_VALUE: pressed ? -32767 : 0, PRESSED: input.R_STICK.PRESSED };
      if (code === 'ArrowLeft') updates.R_STICK = { ...input.R_STICK, X_VALUE: pressed ? -32767 : 0, PRESSED: input.R_STICK.PRESSED };
      if (code === 'ArrowRight') updates.R_STICK = { ...input.R_STICK, X_VALUE: pressed ? 32767 : 0, PRESSED: input.R_STICK.PRESSED };
      if (key === 'Y') updates.R_STICK = { ...input.R_STICK, PRESSED: pressed };

      // Dpad
      if (key === 'G') updates.DPAD_UP = pressed;
      if (key === 'V') updates.DPAD_LEFT = pressed;
      if (key === 'B') updates.DPAD_RIGHT = pressed;
      if (key === 'N') updates.DPAD_DOWN = pressed;

      // Triggers/Shoulders
      if (key === '1') updates.L = pressed;
      if (key === '2') updates.ZL = pressed;
      if (key === '8') updates.R = pressed;
      if (key === '9') updates.ZR = pressed;

      // Face Buttons
      if (key === 'L') updates.A = pressed; // A is East
      if (key === 'K') updates.B = pressed; // B is South
      if (key === 'I') updates.X = pressed; // X is North
      if (key === 'J') updates.Y = pressed; // Y is West (Wait, old map says Y is West, check mapping)

      // Meta
      if (key === '6') updates.PLUS = pressed;
      if (key === '7') updates.MINUS = pressed;
      if (key === '[') updates.HOME = pressed;
      if (key === ']') updates.CAPTURE = pressed;

      if (Object.keys(updates).length > 0) {
        updateInput(updates);
      }
    };

    const down = (e: KeyboardEvent) => handleKey(e, true);
    const up = (e: KeyboardEvent) => handleKey(e, false);

    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);

    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
    };
  }, [input, index]); // Re-bind when input changes to have fresh state closure

  // Button handlers
  const handleBtn = (key: keyof DirectInputPacket, pressed: boolean) => {
    if (input[key] !== pressed) {
      updateInput({ [key]: pressed } as any);
    }
  };

  return (
    <div className="flex flex-col gap-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg select-none transition-colors duration-300">
      {/* Shoulders */}
      <div className="flex justify-between px-8">
        <div className="flex gap-2">
          <Btn label="ZL" active={input.ZL} onToggle={(v) => handleBtn('ZL', v)} />
          <Btn label="L" active={input.L} onToggle={(v) => handleBtn('L', v)} />
        </div>
        <div className="flex gap-2">
          <Btn label="R" active={input.R} onToggle={(v) => handleBtn('R', v)} />
          <Btn label="ZR" active={input.ZR} onToggle={(v) => handleBtn('ZR', v)} />
        </div>
      </div>

      <div className="flex justify-around items-center">
        {/* Left Stick & Dpad */}
        <div className="flex flex-col gap-4">
            <div className="relative w-24 h-24 bg-slate-200 dark:bg-slate-700 rounded-full border border-slate-300 dark:border-slate-600 flex items-center justify-center transition-colors">
                <span className="text-xs text-slate-400 dark:text-slate-500">L-Stick</span>
                <button 
                  onMouseDown={() => {
                     const s = { ...input.L_STICK, PRESSED: true };
                     updateInput({ L_STICK: s });
                  }}
                  onMouseUp={() => {
                     const s = { ...input.L_STICK, PRESSED: false };
                     updateInput({ L_STICK: s });
                  }}
                  className={`absolute w-8 h-8 rounded-full transition-colors ${input.L_STICK.PRESSED ? 'bg-honey-500' : 'bg-slate-400 dark:bg-slate-600'}`}
                />
            </div>

            <div className="grid grid-cols-3 gap-1 w-24">
                <div />
                <Btn icon={<ArrowUp size={16}/>} active={input.DPAD_UP} onToggle={(v) => handleBtn('DPAD_UP', v)} />
                <div />
                <Btn icon={<ArrowLeft size={16}/>} active={input.DPAD_LEFT} onToggle={(v) => handleBtn('DPAD_LEFT', v)} />
                <div />
                <Btn icon={<ArrowRight size={16}/>} active={input.DPAD_RIGHT} onToggle={(v) => handleBtn('DPAD_RIGHT', v)} />
                <div />
                <Btn icon={<ArrowDown size={16}/>} active={input.DPAD_DOWN} onToggle={(v) => handleBtn('DPAD_DOWN', v)} />
                <div />
            </div>
        </div>

        {/* Center */}
        <div className="flex flex-col gap-6 pt-8">
            <div className="flex gap-4">
                <Btn label="-" active={input.MINUS} onToggle={(v) => handleBtn('MINUS', v)} circle />
                <Btn label="+" active={input.PLUS} onToggle={(v) => handleBtn('PLUS', v)} circle />
            </div>
            <div className="flex gap-4 justify-center">
                <Btn label="Capture" active={input.CAPTURE} onToggle={(v) => handleBtn('CAPTURE', v)} square />
                <Btn label="Home" active={input.HOME} onToggle={(v) => handleBtn('HOME', v)} circle />
            </div>
        </div>

        {/* Right Stick & Face Buttons */}
        <div className="flex flex-col gap-4">
            <div className="grid grid-cols-3 gap-2 w-24 mb-4">
                <div />
                <Btn label="X" active={input.X} onToggle={(v) => handleBtn('X', v)} round />
                <div />
                <Btn label="Y" active={input.Y} onToggle={(v) => handleBtn('Y', v)} round />
                <div />
                <Btn label="A" active={input.A} onToggle={(v) => handleBtn('A', v)} round />
                <div />
                <Btn label="B" active={input.B} onToggle={(v) => handleBtn('B', v)} round />
                <div />
            </div>

             <div className="relative w-24 h-24 bg-slate-200 dark:bg-slate-700 rounded-full border border-slate-300 dark:border-slate-600 flex items-center justify-center transition-colors">
                <span className="text-xs text-slate-400 dark:text-slate-500">R-Stick</span>
                 <button 
                  onMouseDown={() => {
                     const s = { ...input.R_STICK, PRESSED: true };
                     updateInput({ R_STICK: s });
                  }}
                  onMouseUp={() => {
                     const s = { ...input.R_STICK, PRESSED: false };
                     updateInput({ R_STICK: s });
                  }}
                  className={`absolute w-8 h-8 rounded-full transition-colors ${input.R_STICK.PRESSED ? 'bg-honey-500' : 'bg-slate-400 dark:bg-slate-600'}`}
                />
            </div>
        </div>
      </div>
    </div>
  );
};

interface BtnProps {
  label?: string;
  icon?: React.ReactNode;
  active: boolean;
  onToggle: (pressed: boolean) => void;
  round?: boolean;
  circle?: boolean;
  square?: boolean;
}

const Btn: React.FC<BtnProps> = ({ label, icon, active, onToggle, round, circle, square }) => {
  return (
    <button
      onMouseDown={() => onToggle(true)}
      onMouseUp={() => onToggle(false)}
      onMouseLeave={() => onToggle(false)}
      onTouchStart={(e) => { e.preventDefault(); onToggle(true); }}
      onTouchEnd={(e) => { e.preventDefault(); onToggle(false); }}
      className={`
        flex items-center justify-center font-bold transition-all duration-75
        ${active ? 'bg-honey-400 text-white shadow-inner scale-95 border-honey-500' : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 shadow-sm hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-600'}
        ${round ? 'w-10 h-10 rounded-full' : ''}
        ${circle ? 'w-8 h-8 rounded-full text-xs' : ''}
        ${square ? 'w-8 h-8 rounded-md text-[10px]' : ''}
        ${!round && !circle && !square ? 'px-3 py-1.5 rounded-md min-w-[3rem]' : ''}
      `}
    >
      {icon || label}
    </button>
  );
};
