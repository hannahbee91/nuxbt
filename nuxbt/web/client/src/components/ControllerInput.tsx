import React, { useState, useEffect, useRef } from 'react';
import type { DirectInputPacket, KeyMap } from '../types';
import { socket } from '../socket';
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from 'lucide-react';
import { DEFAULT_KEYBINDS } from '../defaults';

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
  const [keyMap, setKeyMap] = useState<KeyMap>(DEFAULT_KEYBINDS);
  
  // Refs for loop
  const inputRef = useRef(input);
  const keyMapRef = useRef(keyMap);
  inputRef.current = input;
  keyMapRef.current = keyMap;

  // Track pressed keys for simpler logic
  const pressedKeys = useRef<Set<string>>(new Set());

  // Ref for UI interactions
  const uiState = useRef<Partial<DirectInputPacket>>({});

  // Fetch Keybinds
  useEffect(() => {
      fetch('/api/keybinds')
        .then(res => res.json())
        .then(data => {
            if (data && data.keyboard) {
                setKeyMap(data);
            }
        })
        .catch(err => console.error("Failed to load keybinds", err));
  }, []);

  const updateInput = (newInput: DirectInputPacket) => {
    // Only update if changed (deep compare simplified)
    if (JSON.stringify(newInput) !== JSON.stringify(inputRef.current)) {
        setInput(newInput);
        socket.emit('input', JSON.stringify([parseInt(index), newInput]));
    }
  };

  // Keyboard Handler (Event-based)
  useEffect(() => {
    const handleKey = (e: KeyboardEvent, isDown: boolean) => {
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) return;
      
      const code = e.code;
      if (isDown) pressedKeys.current.add(code);
      else pressedKeys.current.delete(code);
      
      processInput();
    };

    const down = (e: KeyboardEvent) => handleKey(e, true);
    const up = (e: KeyboardEvent) => handleKey(e, false);

    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
    };
  }, []);

  // Gamepad Polling Loop & Processing
  useEffect(() => {
      let animationFrameId: number;

      const loop = () => {
          processInput();
          animationFrameId = requestAnimationFrame(loop);
      };
      
      animationFrameId = requestAnimationFrame(loop);
      return () => cancelAnimationFrame(animationFrameId);
  }, []);

  const processInput = () => {
      const map = keyMapRef.current;
      const keys = pressedKeys.current;
      const gps = navigator.getGamepads ? navigator.getGamepads() : [];
      const gp = gps[0]; // Use first gamepad for now
      
      // Merge UI overrides
      const ui = uiState.current;

      const next = JSON.parse(JSON.stringify(EMPTY_PACKET));
      const getAction = (action: string): boolean => {
          // Check Keyboard
          if (map.keyboard[action] && keys.has(map.keyboard[action])) return true;
          
          // Check Gamepad
          if (gp && map.gamepad) {
              // Button
              if (map.gamepad.buttons[action] !== undefined) {
                  const btn = gp.buttons[map.gamepad.buttons[action]];
                  if (btn && btn.pressed) return true;
              }
              // Axis as Button (e.g. L_STICK_UP on axis)
               if (map.gamepad.axes[action] !== undefined) {
                  const def = map.gamepad.axes[action];
                  const val = gp.axes[def.index];
                  if (def.direction === 1 && val > 0.5) return true;
                  if (def.direction === -1 && val < -0.5) return true;
              }
          }
          return false;
      };

      // Map basic buttons
      // Logic: (Keyboard || Gamepad || UI)
      next.A = getAction('A') || !!ui.A;
      next.B = getAction('B') || !!ui.B;
      next.X = getAction('X') || !!ui.X;
      next.Y = getAction('Y') || !!ui.Y;
      next.L = getAction('L') || !!ui.L;
      next.R = getAction('R') || !!ui.R;
      next.ZL = getAction('ZL') || !!ui.ZL;
      next.ZR = getAction('ZR') || !!ui.ZR;
      next.PLUS = getAction('PLUS') || !!ui.PLUS;
      next.MINUS = getAction('MINUS') || !!ui.MINUS;
      next.HOME = getAction('HOME') || !!ui.HOME;
      next.CAPTURE = getAction('CAPTURE') || !!ui.CAPTURE;
      next.DPAD_UP = getAction('DPAD_UP') || !!ui.DPAD_UP;
      next.DPAD_DOWN = getAction('DPAD_DOWN') || !!ui.DPAD_DOWN;
      next.DPAD_LEFT = getAction('DPAD_LEFT') || !!ui.DPAD_LEFT;
      next.DPAD_RIGHT = getAction('DPAD_RIGHT') || !!ui.DPAD_RIGHT;
      next.L_STICK.PRESSED = getAction('L_STICK_PRESS') || (ui.L_STICK?.PRESSED || false);
      next.R_STICK.PRESSED = getAction('R_STICK_PRESS') || (ui.R_STICK?.PRESSED || false);

      // Analog Sticks Logic
      // Combine digital inputs (keys) + Analog inputs (gamepad axes)
      const processStick = (prefix: string, uiStick?: any): [number, number] => {
          let x = 0; 
          let y = 0;
          
          // Digital (Keyboard / Dpad-mapped axes)
          if (getAction(`${prefix}_UP`)) y += 32767;
          if (getAction(`${prefix}_DOWN`)) y -= 32767;
          if (getAction(`${prefix}_LEFT`)) x -= 32767;
          if (getAction(`${prefix}_RIGHT`)) x += 32767;
          
          if (uiStick) {
             // UI probably doesn't set X/Y but could
             if (uiStick.X_VALUE) x = uiStick.X_VALUE;
             if (uiStick.Y_VALUE) y = uiStick.Y_VALUE;
          }

          // Analog Overrides if gamepad present
          if (gp && map.gamepad) {
              const dz = 0.1;
              if (prefix === 'L_STICK') {
                  if (Math.abs(gp.axes[0]) > dz) x = gp.axes[0] * 32767;
                  if (Math.abs(gp.axes[1]) > dz) y = gp.axes[1] * -32767; // Y inverted
              } else {
                  if (Math.abs(gp.axes[2]) > dz) x = gp.axes[2] * 32767;
                  if (Math.abs(gp.axes[3]) > dz) y = gp.axes[3] * -32767;
              }
          }
          
          // Clamp
          x = Math.max(-32767, Math.min(32767, x));
          y = Math.max(-32767, Math.min(32767, y));
          return [x, y];
      };
      
      [next.L_STICK.X_VALUE, next.L_STICK.Y_VALUE] = processStick('L_STICK', ui.L_STICK);
      [next.R_STICK.X_VALUE, next.R_STICK.Y_VALUE] = processStick('R_STICK', ui.R_STICK);

      updateInput(next);
  };

  return (
    <div className="flex flex-col gap-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg select-none transition-colors duration-300">
      <div className="flex justify-between px-8">
        <div className="flex gap-2">
          <Btn label="ZL" active={input.ZL} onToggle={(v) => uiState.current.ZL = v} />
          <Btn label="L" active={input.L} onToggle={(v) => uiState.current.L = v} />
        </div>
        <div className="flex gap-2">
          <Btn label="R" active={input.R} onToggle={(v) => uiState.current.R = v} />
          <Btn label="ZR" active={input.ZR} onToggle={(v) => uiState.current.ZR = v} />
        </div>
      </div>

      <div className="flex justify-around items-center">
        {/* Left Stick & Dpad */}
        <div className="flex flex-col gap-4">
            <div className="relative w-24 h-24 bg-slate-200 dark:bg-slate-700 rounded-full border border-slate-300 dark:border-slate-600 flex items-center justify-center transition-colors">
                <span className="text-xs text-slate-400 dark:text-slate-500">L-Stick</span>
                <button 
                  onMouseDown={() => { if(uiState.current.L_STICK) uiState.current.L_STICK.PRESSED = true; else uiState.current.L_STICK = {PRESSED: true, X_VALUE:0, Y_VALUE:0}; }}
                  onMouseUp={() => { if(uiState.current.L_STICK) uiState.current.L_STICK.PRESSED = false; }}
                  className={`absolute w-8 h-8 rounded-full transition-colors ${input.L_STICK.PRESSED ? 'bg-honey-500' : 'bg-slate-400 dark:bg-slate-600'}`}
                />
            </div>

            <div className="grid grid-cols-3 gap-1 w-24">
                <div />
                <Btn icon={<ArrowUp size={16}/>} active={input.DPAD_UP} onToggle={(v) => uiState.current.DPAD_UP = v} />
                <div />
                <Btn icon={<ArrowLeft size={16}/>} active={input.DPAD_LEFT} onToggle={(v) => uiState.current.DPAD_LEFT = v} />
                <div />
                <Btn icon={<ArrowRight size={16}/>} active={input.DPAD_RIGHT} onToggle={(v) => uiState.current.DPAD_RIGHT = v} />
                <div />
                <Btn icon={<ArrowDown size={16}/>} active={input.DPAD_DOWN} onToggle={(v) => uiState.current.DPAD_DOWN = v} />
                <div />
            </div>
        </div>

        {/* Center */}
        <div className="flex flex-col gap-6 pt-8">
            <div className="flex gap-4">
                <Btn label="-" active={input.MINUS} onToggle={(v) => uiState.current.MINUS = v} circle />
                <Btn label="+" active={input.PLUS} onToggle={(v) => uiState.current.PLUS = v} circle />
            </div>
            <div className="flex gap-4 justify-center">
                <Btn label="Capture" active={input.CAPTURE} onToggle={(v) => uiState.current.CAPTURE = v} square />
                <Btn label="Home" active={input.HOME} onToggle={(v) => uiState.current.HOME = v} circle />
            </div>
        </div>

        {/* Right Stick & Face Buttons */}
        <div className="flex flex-col gap-4">
            <div className="grid grid-cols-3 gap-2 w-24 mb-4">
                <div />
                <Btn label="X" active={input.X} onToggle={(v) => uiState.current.X = v} round />
                <div />
                <Btn label="Y" active={input.Y} onToggle={(v) => uiState.current.Y = v} round />
                <div />
                <Btn label="A" active={input.A} onToggle={(v) => uiState.current.A = v} round />
                <div />
                <Btn label="B" active={input.B} onToggle={(v) => uiState.current.B = v} round />
                <div />
            </div>

             <div className="relative w-24 h-24 bg-slate-200 dark:bg-slate-700 rounded-full border border-slate-300 dark:border-slate-600 flex items-center justify-center transition-colors">
                <span className="text-xs text-slate-400 dark:text-slate-500">R-Stick</span>
                 <button 
                  onMouseDown={() => { if(uiState.current.R_STICK) uiState.current.R_STICK.PRESSED = true; else uiState.current.R_STICK = {PRESSED: true, X_VALUE:0, Y_VALUE:0}; }}
                  onMouseUp={() => { if(uiState.current.R_STICK) uiState.current.R_STICK.PRESSED = false; }}
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
