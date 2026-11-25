import { ref, readonly } from 'vue'

/**
 * useRoomChrome
 *
 * Shared singleton state that lets the global navbar (App.vue) show and drive
 * the room's own controls — Leave Room and Admin Controls — without App.vue
 * needing to know anything about Room.vue's internals.
 *
 * Room.vue calls registerRoomChrome() on mount and clears it on unmount;
 * App.vue reads the flags and invokes the handlers.
 */
const inRoom = ref(false)
const isRoomAdmin = ref(false)
// 'board' or 'table'
const roomView = ref('board')

let handlers = { onLeaveRoom: null, onOpenAdminControls: null, onSetView: null }

export function registerRoomChrome({ onLeaveRoom, onOpenAdminControls, onSetView }) {
  handlers = { onLeaveRoom, onOpenAdminControls, onSetView }
  inRoom.value = true
}

export function clearRoomChrome() {
  handlers = { onLeaveRoom: null, onOpenAdminControls: null, onSetView: null }
  inRoom.value = false
  isRoomAdmin.value = false
}

export function setRoomView(mode) {
  roomView.value = mode === 'table' ? 'table' : 'board'
}

export function setRoomAdmin(value) {
  isRoomAdmin.value = Boolean(value)
}

export function useRoomChrome() {
  return {
    inRoom: readonly(inRoom),
    isRoomAdmin: readonly(isRoomAdmin),
    roomView: readonly(roomView),
    setView: (mode) => handlers.onSetView && handlers.onSetView(mode),
    leaveRoom: () => handlers.onLeaveRoom && handlers.onLeaveRoom(),
    openAdminControls: () => handlers.onOpenAdminControls && handlers.onOpenAdminControls()
  }
}
