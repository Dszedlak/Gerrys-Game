<template>
  <BForm @submit.prevent="onSubmit">
    <BFormGroup label="Username" label-for="username-input">
      <BFormInput
        id="username-input"
        v-model="username"
        required
        placeholder="Enter username"
      />
    </BFormGroup>
    <BFormGroup label="Password" label-for="password-input">
      <BFormInput
        id="password-input"
        v-model="password"
        type="password"
        required
        placeholder="Enter password"
      />
    </BFormGroup>
    <div class="mb-2">
      <small v-if="error" class="text-danger">{{ error }}</small>
    </div>
    <BButton type="submit" variant="primary" :disabled="loading">
      Login
    </BButton>
  </BForm>
</template>

<script>
import { ref } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { BForm, BFormGroup, BFormInput, BButton } from 'bootstrap-vue-next'

export default {
  components: { BForm, BFormGroup, BFormInput, BButton },
  setup() {
    const store = useStore()
    const router = useRouter()
    const username = ref('')
    const password = ref('')
    const error = ref('')
    const loading = ref(false)

    const onSubmit = () => {
      error.value = ''
      loading.value = true
      store.dispatch('auth/login', { username: username.value, password: password.value })
        .then(({ data }) => {
          context.commit('setUser', {
            username: data.username, // use backend username
            token: data.token
          });
          resolve(data);
        })
        .catch(err => {
          error.value = store.state.auth.errors || 'Login failed'
        })
        .finally(() => {
          loading.value = false
        })
    }

    return { username, password, error, loading, onSubmit }
  }
}
</script>
