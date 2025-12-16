import React, { useRef, useEffect } from 'react';
import type { DirectInputPacket } from '../types';
import { socket } from '../socket';
import proControllerSvg from '../assets/pro-controller.svg';

interface Props {
  index: string;
  input: DirectInputPacket;
  setInput: (input: DirectInputPacket) => void;
}

export const ControllerVisual: React.FC<Props> = ({ index, input, setInput }) => {
  const keysHeld = useRef<Set<string>>(new Set());
  const rafRef = useRef<number>(0);
  const lastInputRef = useRef<string>(JSON.stringify(input));
  const inputRef = useRef(input); 

  useEffect(() => { inputRef.current = input; }, [input]);

  // --- Input Loop (Keyboard + Gamepad Only) ---
  useEffect(() => {
    const updateLoop = () => {
        const keys = keysHeld.current;
        
        // 1. Keyboard Stick Influence
        let kLx = 0, kLy = 0;
        if (keys.has('W')) kLy += 100;
        if (keys.has('S')) kLy -= 100;
        if (keys.has('A')) kLx -= 100;
        if (keys.has('D')) kLx += 100;

        let kRx = 0, kRy = 0;
        if (keys.has('ArrowUp')) kRy += 100;
        if (keys.has('ArrowDown')) kRy -= 100;
        if (keys.has('ArrowLeft')) kRx -= 100;
        if (keys.has('ArrowRight')) kRx += 100;

        // 2. Gamepad Influence
        const gp = navigator.getGamepads()[0];
        let gLx = 0, gLy = 0, gRx = 0, gRy = 0;
        
        let gpButtons = {
            A: false, B: false, X: false, Y: false,
            L: false, R: false, ZL: false, ZR: false,
            Minus: false, Plus: false, L3: false, R3: false,
            Home: false, Cap: false,
            Up: false, Down: false, Left: false, Right: false
        };

        if (gp) {
            // Axes
            gLx = gp.axes[0] * 100;
            gLy = gp.axes[1] * -100; // Invert Y
            gRx = gp.axes[2] * 100;
            gRy = gp.axes[3] * -100;

            const DZ = 15;
            if (Math.abs(gLx) < DZ) gLx = 0;
            if (Math.abs(gLy) < DZ) gLy = 0;
            if (Math.abs(gRx) < DZ) gRx = 0;
            if (Math.abs(gRy) < DZ) gRy = 0;

            // Buttons (Standard Mapping)
            gpButtons.B = gp.buttons[0].pressed; 
            gpButtons.A = gp.buttons[1].pressed;
            gpButtons.Y = gp.buttons[2].pressed;
            gpButtons.X = gp.buttons[3].pressed;
            gpButtons.L = gp.buttons[4].pressed;
            gpButtons.R = gp.buttons[5].pressed;
            gpButtons.ZL = gp.buttons[6].pressed;
            gpButtons.ZR = gp.buttons[7].pressed;
            gpButtons.Minus = gp.buttons[8].pressed;
            gpButtons.Plus = gp.buttons[9].pressed;
            gpButtons.L3 = gp.buttons[10].pressed;
            gpButtons.R3 = gp.buttons[11].pressed;
            gpButtons.Up = gp.buttons[12].pressed;
            gpButtons.Down = gp.buttons[13].pressed;
            gpButtons.Left = gp.buttons[14].pressed;
            gpButtons.Right = gp.buttons[15].pressed;
            gpButtons.Home = gp.buttons[16].pressed;
        }

        // Combine
        let finalLx = Math.max(-100, Math.min(100, kLx + gLx));
        let finalLy = Math.max(-100, Math.min(100, kLy + gLy));
        let finalRx = Math.max(-100, Math.min(100, kRx + gRx));
        let finalRy = Math.max(-100, Math.min(100, kRy + gRy));

        // Build Packet (Fresh state based on inputs)
        const packet: DirectInputPacket = { ...inputRef.current }; 

        packet.A = keys.has('L') || gpButtons.A;
        packet.B = keys.has('K') || gpButtons.B;
        packet.X = keys.has('I') || gpButtons.X;
        packet.Y = keys.has('J') || gpButtons.Y;

        packet.L = keys.has('1') || gpButtons.L;
        packet.R = keys.has('8') || gpButtons.R;
        packet.ZL = keys.has('2') || gpButtons.ZL;
        packet.ZR = keys.has('9') || gpButtons.ZR;

        packet.PLUS = keys.has('6') || gpButtons.Plus;
        packet.MINUS = keys.has('7') || gpButtons.Minus;
        packet.HOME = keys.has('[') || gpButtons.Home;
        packet.CAPTURE = keys.has(']') || gpButtons.Cap;

        packet.DPAD_UP = keys.has('G') || gpButtons.Up;
        packet.DPAD_DOWN = keys.has('N') || gpButtons.Down;
        packet.DPAD_LEFT = keys.has('V') || gpButtons.Left;
        packet.DPAD_RIGHT = keys.has('B') || gpButtons.Right;
        
        packet.L_STICK = { 
            ...packet.L_STICK,
            LS_UP: false, LS_DOWN: false, LS_LEFT: false, LS_RIGHT: false,
            X_VALUE: finalLx, 
            Y_VALUE: finalLy, 
            PRESSED: keys.has('T') || gpButtons.L3
        };
        packet.R_STICK = { 
            ...packet.R_STICK,
            RS_UP: false, RS_DOWN: false, RS_LEFT: false, RS_RIGHT: false,
            X_VALUE: finalRx, 
            Y_VALUE: finalRy, 
            PRESSED: keys.has('Y') || gpButtons.R3
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
  }, [index, setInput]);

  return (
    <div className="relative w-full max-w-[600px] mx-auto select-none pointer-events-none">
        <img src={proControllerSvg} alt="Pro Controller" className="w-full block" />
        {/* No overlays at all, as requested */}
    </div>
  );
};
