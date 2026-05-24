import { render } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ControllerVisual } from './ControllerVisual';
import type { DirectInputPacket, KeyMap, StickState } from '../types';
import { DEFAULT_KEYBINDS } from '../defaults';

// Mock socket
vi.mock('../socket', () => ({
  socket: {
    emit: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
  },
}));

const mockStick: StickState = {
  PRESSED: false,
  X_VALUE: 0,
  Y_VALUE: 0
};

const mockInput: DirectInputPacket = {
  L_STICK: mockStick,
  R_STICK: mockStick,
  DPAD_UP: false,
  DPAD_LEFT: false,
  DPAD_RIGHT: false,
  DPAD_DOWN: false,
  L: false,
  ZL: false,
  R: false,
  ZR: false,
  JCL_SR: false,
  JCL_SL: false,
  JCR_SR: false,
  JCR_SL: false,
  PLUS: false,
  MINUS: false,
  HOME: false,
  CAPTURE: false,
  Y: false,
  X: false,
  B: false,
  A: false
};

describe('ControllerVisual', () => {
  let mockGamepad: any;

  beforeEach(() => {
    vi.useFakeTimers();
    mockGamepad = {
      axes: [0, 0, 0, 0],
      buttons: Array(17).fill(null).map(() => ({ pressed: false, touched: false, value: 0 })),
      mapping: 'standard'
    };
    vi.stubGlobal('navigator', {
      getGamepads: vi.fn(() => [mockGamepad])
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('renders without crashing and responds to standard gamepad button press', async () => {
    const setInputMock = vi.fn();
    
    // Press button 'A' (Standard mapping index 1)
    mockGamepad.buttons[1].pressed = true;

    render(
      <ControllerVisual 
        index="0" 
        input={mockInput} 
        setInput={setInputMock} 
        keyMap={DEFAULT_KEYBINDS}
      />
    );

    // Trigger animation frame loop
    await vi.advanceTimersByTimeAsync(16);

    expect(setInputMock).toHaveBeenCalled();
    const lastCalled = setInputMock.mock.calls[setInputMock.mock.calls.length - 1][0];
    expect(lastCalled.A).toBe(true);
    expect(lastCalled.B).toBe(false);
  });

  it('correctly maps non-standard gamepad buttons and axes', async () => {
    const setInputMock = vi.fn();
    
    // Custom key map representing a raw non-standard mapping where:
    // - D-Pad Up is mapped to Axis 5 negative direction (-1)
    // - D-Pad Down is mapped to Axis 5 positive direction (1)
    // - Right Stick Press (R3) is mapped to Button 14
    const customKeyMap: KeyMap = {
      keyboard: { ...DEFAULT_KEYBINDS.keyboard },
      gamepad: {
        buttons: {
          ...DEFAULT_KEYBINDS.gamepad.buttons,
          'R_STICK_PRESS': 14,
        },
        axes: {
          ...DEFAULT_KEYBINDS.gamepad.axes,
          'DPAD_UP': { index: 5, direction: -1 },
          'DPAD_DOWN': { index: 5, direction: 1 },
        }
      }
    };

    // Press custom R3 button (index 14) and trigger DPAD_DOWN axis (index 5 val 0.8)
    mockGamepad.buttons[14] = { pressed: true };
    mockGamepad.axes[5] = 0.8;

    render(
      <ControllerVisual 
        index="0" 
        input={mockInput} 
        setInput={setInputMock} 
        keyMap={customKeyMap}
      />
    );

    // Trigger animation frame loop
    await vi.advanceTimersByTimeAsync(16);

    expect(setInputMock).toHaveBeenCalled();
    const lastCalled = setInputMock.mock.calls[setInputMock.mock.calls.length - 1][0];
    expect(lastCalled.R_STICK.PRESSED).toBe(true);
    expect(lastCalled.DPAD_DOWN).toBe(true);
    expect(lastCalled.DPAD_UP).toBe(false);
  });
});
