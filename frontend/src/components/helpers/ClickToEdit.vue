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
    export default {
    
    props: ['value'],
    
    data () {
      
    return {
        edit: false,
        valueLocal: this.value,
        oldValue: (' ' + this.value).slice(1)
      }
    },
    methods: {
        save(event){
          if(event.target.value){             
              this.valueLocal = event.target.value; 
              this.edit = false; 
              this.$emit('input', this.valueLocal);
          }
        },
        esc(event){
            this.valueLocal = this.oldValue; 
            event.target.value = this.oldValue;
            this.edit = false; 
            this.$emit('input', this.valueLocal);
        }
    },
    watch: {
      value: function() {
        this.valueLocal = this.value;
      }
    },
    
    directives: {
      focus: {
          inserted (el) {
              el.focus()
          }
      }
    }
    
  }
  </script>
<style>
.my-checkbox {
    font-size: 2em;
    color: rgb(64, 224, 64);
}

.input-checkbox {
    font-size: 1em;
    text-align: center;
    color: rgb(64, 224, 64);
}
</style>