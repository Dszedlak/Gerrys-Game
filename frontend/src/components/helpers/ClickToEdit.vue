<template>
    <span class="my-checkbox">
      <input class="input-checkbox" type="text"
             v-if="edit"
             :value="valueLocal"
             @blur="save($event);"
             @keyup.enter="save($event);"
             @keyup.esc="esc($event);"
             @input="onInput"
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
        onInput(event) {
          // If this is the clock field, restrict to numbers only
          if (this.action === 'updateClock') {
            event.target.value = event.target.value.replace(/[^0-9•]/g, '')
            this.valueLocal = event.target.value
          } else {
            this.valueLocal = event.target.value
          }
        },
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
    color: #EAB308;;
}

.input-checkbox {
    font-size: 1em;
    text-align: center;
    color: #EAB308;
    background: #1A1F2E;
    border: 2px solid rgba(145, 70, 255, 0.3);
    border-radius: 6px;
    padding: 8px 12px;
    transition: all 0.3s ease;;
}

.input-checkbox:focus {
    outline: none;
    border-color: #EAB308;;
}
</style>













