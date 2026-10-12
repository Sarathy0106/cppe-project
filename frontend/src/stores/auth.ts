import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
} from 'amazon-cognito-identity-js'
import { CONFIG } from '../config'

const poolData = {
  UserPoolId: CONFIG.USER_POOL_ID,
  ClientId: CONFIG.CLIENT_ID,
}
const userPool = new CognitoUserPool(poolData)

export interface UserProfile {
  email: string
  sub: string
  groups: string[]
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('cv_token'))
  const user = ref<UserProfile | null>(
    localStorage.getItem('cv_user')
      ? JSON.parse(localStorage.getItem('cv_user')!)
      : null
  )

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.groups?.includes('Admin') ?? false)
  const isViewer = computed(() => user.value?.groups?.includes('Viewer') ?? false)

  function parseJwt(jwtToken: string): any {
    try {
      const base64Url = jwtToken.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
      return JSON.parse(jsonPayload)
    } catch {
      return {}
    }
  }

  function setSession(idToken: string) {
    token.value = idToken
    localStorage.setItem('cv_token', idToken)

    const claims = parseJwt(idToken)
    let groups: string[] = []
    if (claims['cognito:groups']) {
      groups = Array.isArray(claims['cognito:groups'])
        ? claims['cognito:groups']
        : [claims['cognito:groups']]
    }

    const profile: UserProfile = {
      email: claims.email || '',
      sub: claims.sub || '',
      groups,
    }
    user.value = profile
    localStorage.setItem('cv_user', JSON.stringify(profile))
  }

  function login(username: string, password: string): Promise<UserProfile> {
    return new Promise((resolve, reject) => {
      const authDetails = new AuthenticationDetails({
        Username: username.trim(),
        Password: password,
      })

      const cognitoUser = new CognitoUser({
        Username: username.trim(),
        Pool: userPool,
      })

      cognitoUser.authenticateUser(authDetails, {
        onSuccess: (result) => {
          const idToken = result.getIdToken().getJwtToken()
          setSession(idToken)
          resolve(user.value!)
        },
        onFailure: (err) => {
          reject(err)
        },
        newPasswordRequired: (userAttributes) => {
          // If password reset required on first login
          cognitoUser.completeNewPasswordChallenge(password, userAttributes, {
            onSuccess: (result) => {
              const idToken = result.getIdToken().getJwtToken()
              setSession(idToken)
              resolve(user.value!)
            },
            onFailure: (err) => {
              reject(err)
            },
          })
        },
      })
    })
  }

  function logout() {
    const currentUser = userPool.getCurrentUser()
    if (currentUser) {
      currentUser.signOut()
    }
    token.value = null
    user.value = null
    localStorage.removeItem('cv_token')
    localStorage.removeItem('cv_user')
  }

  return {
    token,
    user,
    isAuthenticated,
    isAdmin,
    isViewer,
    login,
    logout,
  }
})
