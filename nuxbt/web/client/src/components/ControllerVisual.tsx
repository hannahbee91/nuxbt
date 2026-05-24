import React, { useRef, useEffect } from 'react';
import type { DirectInputPacket, KeyMap } from '../types';
import { socket } from '../socket';
import proControllerSvg from '../assets/pro-controller.svg';

interface Props {
  index: string;
  input: DirectInputPacket;
  setInput: (input: DirectInputPacket) => void;
  keyMap: KeyMap;
}

export const ControllerVisual: React.FC<Props> = ({ index, input, setInput, keyMap }) => {
  const keysHeld = useRef<Set<string>>(new Set());
  const rafRef = useRef<number>(0);
  const lastInputRef = useRef<string>(JSON.stringify(input));
  const inputRef = useRef(input); 

  useEffect(() => { inputRef.current = input; }, [input]);

  // --- Input Loop (Keyboard + Gamepad Only) ---
  useEffect(() => {
    const updateLoop = () => {
        const keys = keysHeld.current;
        
        // 1. Keyboard Stick Influence (from keyMap bindings)
        let kLx = 0, kLy = 0;
        if (keyMap.keyboard['L_STICK_UP'] && keys.has(keyMap.keyboard['L_STICK_UP'])) kLy += 100;
        if (keyMap.keyboard['L_STICK_DOWN'] && keys.has(keyMap.keyboard['L_STICK_DOWN'])) kLy -= 100;
        if (keyMap.keyboard['L_STICK_LEFT'] && keys.has(keyMap.keyboard['L_STICK_LEFT'])) kLx -= 100;
        if (keyMap.keyboard['L_STICK_RIGHT'] && keys.has(keyMap.keyboard['L_STICK_RIGHT'])) kLx += 100;

        let kRx = 0, kRy = 0;
        if (keyMap.keyboard['R_STICK_UP'] && keys.has(keyMap.keyboard['R_STICK_UP'])) kRy += 100;
        if (keyMap.keyboard['R_STICK_DOWN'] && keys.has(keyMap.keyboard['R_STICK_DOWN'])) kRy -= 100;
        if (keyMap.keyboard['R_STICK_LEFT'] && keys.has(keyMap.keyboard['R_STICK_LEFT'])) kRx -= 100;
        if (keyMap.keyboard['R_STICK_RIGHT'] && keys.has(keyMap.keyboard['R_STICK_RIGHT'])) kRx += 100;

        // 2. Gamepad Influence (dynamic axis & button resolution based on keyMap)
        const gps = navigator.getGamepads ? navigator.getGamepads() : [];
        const gp = gps[0];
        let gLx = 0, gLy = 0, gRx = 0, gRy = 0;

        const getAction = (action: string): boolean => {
            // Check Keyboard
            if (keyMap.keyboard[action] && keys.has(keyMap.keyboard[action])) return true;
            
            // Check Gamepad
            if (gp && keyMap.gamepad) {
                // Button
                if (keyMap.gamepad.buttons[action] !== undefined) {
                    const btn = gp.buttons[keyMap.gamepad.buttons[action]];
                    if (btn && btn.pressed) return true;
                }
                // Axis as Button (e.g. DPAD as axis or trigger threshold)
                if (keyMap.gamepad.axes[action] !== undefined) {
                    const def = keyMap.gamepad.axes[action];
                    if (def && gp.axes[def.index] !== undefined) {
                        const val = gp.axes[def.index];
                        if (def.direction === 1 && val > 0.5) return true;
                        if (def.direction === -1 && val < -0.5) return true;
                    }
                }
            }
            return false;
        };

        if (gp && keyMap.gamepad?.axes) {
            // Left Stick X
            const lsl = keyMap.gamepad.axes['L_STICK_LEFT'];
            const lsr = keyMap.gamepad.axes['L_STICK_RIGHT'];
            if (lsl && lsr && lsl.index === lsr.index && gp.axes[lsl.index] !== undefined) {
                gLx = gp.axes[lsl.index] * 100 * lsr.direction;
            }
            // Left Stick Y
            const lsu = keyMap.gamepad.axes['L_STICK_UP'];
            const lsd = keyMap.gamepad.axes['L_STICK_DOWN'];
            if (lsu && lsd && lsu.index === lsd.index && gp.axes[lsu.index] !== undefined) {
                gLy = gp.axes[lsu.index] * 100 * lsu.direction;
            }
            // Right Stick X
            const rsl = keyMap.gamepad.axes['R_STICK_LEFT'];
            const rsr = keyMap.gamepad.axes['R_STICK_RIGHT'];
            if (rsl && rsr && rsl.index === rsr.index && gp.axes[rsl.index] !== undefined) {
                gRx = gp.axes[rsl.index] * 100 * rsr.direction;
            }
            // Right Stick Y
            const rsu = keyMap.gamepad.axes['R_STICK_UP'];
            const rsd = keyMap.gamepad.axes['R_STICK_DOWN'];
            if (rsu && rsd && rsu.index === rsd.index && gp.axes[rsu.index] !== undefined) {
                gRy = gp.axes[rsu.index] * 100 * rsu.direction;
            }

            // Apply Stick Deadzones
            const DZ = 15;
            if (Math.abs(gLx) < DZ) gLx = 0;
            if (Math.abs(gLy) < DZ) gLy = 0;
            if (Math.abs(gRx) < DZ) gRx = 0;
            if (Math.abs(gRy) < DZ) gRy = 0;
        }

        // Combine Keyboard & Gamepad
        let finalLx = Math.max(-100, Math.min(100, kLx + gLx));
        let finalLy = Math.max(-100, Math.min(100, kLy + gLy));
        let finalRx = Math.max(-100, Math.min(100, kRx + gRx));
        let finalRy = Math.max(-100, Math.min(100, kRy + gRy));

        // Build Packet (Fresh state based on dynamic bindings)
        const packet: DirectInputPacket = { ...inputRef.current }; 

        packet.A = getAction('A');
        packet.B = getAction('B');
        packet.X = getAction('X');
        packet.Y = getAction('Y');

        packet.L = getAction('L');
        packet.R = getAction('R');
        packet.ZL = getAction('ZL');
        packet.ZR = getAction('ZR');

        packet.PLUS = getAction('PLUS');
        packet.MINUS = getAction('MINUS');
        packet.HOME = getAction('HOME');
        packet.CAPTURE = getAction('CAPTURE');

        packet.DPAD_UP = getAction('DPAD_UP');
        packet.DPAD_DOWN = getAction('DPAD_DOWN');
        packet.DPAD_LEFT = getAction('DPAD_LEFT');
        packet.DPAD_RIGHT = getAction('DPAD_RIGHT');
        
        packet.L_STICK = { 
            ...packet.L_STICK,
            LS_UP: false, LS_DOWN: false, LS_LEFT: false, LS_RIGHT: false,
            X_VALUE: finalLx, 
            Y_VALUE: finalLy, 
            PRESSED: getAction('L_STICK_PRESS')
        };
        packet.R_STICK = { 
            ...packet.R_STICK,
            RS_UP: false, RS_DOWN: false, RS_LEFT: false, RS_RIGHT: false,
            X_VALUE: finalRx, 
            Y_VALUE: finalRy, 
            PRESSED: getAction('R_STICK_PRESS')
        };

        const newStr = JSON.stringify(packet);
        if (newStr !== lastInputRef.current) {
            setInput(packet);
            socket.emit('input', JSON.stringify([parseInt(index), packet]));
            lastInputRef.current = newStr;
        }

        rafRef.current = requestAnimationFrame(updateLoop);
    };

    rafRef.current = requestAnimationFrame(updateLoop);

    const down = (e: KeyboardEvent) => { 
        if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return;
        keysHeld.current.add(e.key.toUpperCase()); 
        if(e.code) keysHeld.current.add(e.code);
    };
    const up = (e: KeyboardEvent) => { 
        keysHeld.current.delete(e.key.toUpperCase()); 
        if(e.code) keysHeld.current.delete(e.code);
    };

    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);

    return () => {
        window.removeEventListener('keydown', down);
        window.removeEventListener('keyup', up);
        cancelAnimationFrame(rafRef.current);
    };
  }, [index, setInput, keyMap]);

  return (
    <div className="relative w-full max-w-[600px] mx-auto select-none pointer-events-none">
        <img src={proControllerSvg} alt="Pro Controller" className="w-full block" />
        {/* No overlays at all, as requested */}
    </div>
  );
};
