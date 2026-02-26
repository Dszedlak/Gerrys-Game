<template>
    <span class="my-checkbox">
      <input class="input-checkbox" type="text"
             v-if="edit"
             :value="valueLocal"
             @blur="save($event);"
             @keyup.enter="save($event);"
             @keyup.esc="esc($event);"
             v-focus=""/>
          <span v-else @click="edit = true;">
            {{valueLocal}}
          </span>
      </span>
  </template>
  <script>
    import { useSocket } from '@/composables/useSocket'
    
    export default {
    
    props: ['value', 'action'],
    
    setup() {
      const { socket } = useSocket()
      return { socket }
    },
    
    data () {
      
    return {
        edit: false,
        valueLocal: this.value,
        eventname: this.action,
        oldValue: (' ' + this.value).slice(1)
      }
    },
    methods: {
        save(event){
          if(event.target.value){             
              this.valueLocal = event.target.value;
              this.edit = false; 
              this.$emit('input', this.valueLocal)
              this.socket.emit(this.action, JSON.stringify(this.valueLocal))
          }
        },
        esc(event){
            this.valueLocal = this.oldValue; 
            event.target.value = this.oldValue;
            this.edit = false; 
            this.$emit('input', this.valueLocal);
            this.socket.emit(this.action, JSON.stringify(event.target.value))
        }
    },
    watch: {
      value: function() {
        this.valueLocal = this.value;
        this.eventname = this.action;
      }
    },
    
    directives: {
      focus: {
          mounted (el) {
              el.focus()
          }
      }
    }
    
  }
  </script>
<style>
.my-checkbox {
    font-size: 2em;
    color: #00ff41;
    text-shadow: 0 0 8px rgba(0, 255, 65, 0.5);
}

.input-checkbox {
    font-size: 1em;
    text-align: center;
    color: #00ff41;
    background: #0a0e27;
    border: 2px solid rgba(0, 255, 65, 0.3);
    border-radius: 6px;
    padding: 8px 12px;
    transition: all 0.3s ease;
    text-shadow: 0 0 8px rgba(0, 255, 65, 0.3);
}

.input-checkbox:focus {
    outline: none;
    border-color: #00ff41;
    box-shadow: 0 0 15px rgba(0, 255, 65, 0.3), inset 0 0 10px rgba(0, 255, 65, 0.05);
}
</style>