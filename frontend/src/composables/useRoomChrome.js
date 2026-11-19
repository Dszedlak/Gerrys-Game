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

let handlers = { onLeaveRoom: null, onOpenAdminControls: null }

export function registerRoomChrome({ onLeaveRoom, onOpenAdminControls }) {
  handlers = { onLeaveRoom, onOpenAdminControls }
  inRoom.value = true
}

export function clearRoomChrome() {
  handlers = { onLeaveRoom: null, onOpenAdminControls: null }
  inRoom.value = false
  isRoomAdmin.value = false
}

export function setRoomAdmin(value) {
  isRoomAdmin.value = Boolean(value)
}

export function useRoomChrome() {
  return {
    inRoom: readonly(inRoom),
    isRoomAdmin: readonly(isRoomAdmin),
    leaveRoom: () => handlers.onLeaveRoom && handlers.onLeaveRoom(),
    openAdminControls: () => handlers.onOpenAdminControls && handlers.onOpenAdminControls()
  }
}
