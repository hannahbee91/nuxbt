import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MacroControls } from './MacroControls'
import type { DirectInputPacket, ControllerState, StickState } from '../types'

// Mock socket
vi.mock('../socket', () => ({
  socket: {
    emit: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
  },
}))

// Mock fetch
vi.stubGlobal('fetch', vi.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve([]),
    ok: true,
  })
))

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

const mockControllerState: ControllerState = {
  state: 'connected',
  finished_macros: [],
  errors: false,
  direct_input: mockInput,
  type: 'Pro Controller'
};

describe('MacroControls', () => {
  it('renders without crashing', () => {
    render(
      <MacroControls 
        controllerIndex="0" 
        input={mockInput} 
        controllerState={mockControllerState} 
      />
    )
    expect(screen.getByText(/Macro Name/i)).toBeInTheDocument()
    expect(screen.getByText(/Record/i)).toBeInTheDocument()
  })
})
