<script setup lang="ts">
const controls = [
  {
    category: 'Cryptographic Protection',
    items: [
      {
        name: 'AWS KMS Customer Managed Keys (CMKs)',
        detail: 'Dedicated symmetric CMK with annual key rotation for S3 buckets, CloudWatch Logs, and Athena queries.',
        status: 'ENFORCED',
        badge: 'KMS CMK',
      },
      {
        name: 'RSA-2048 Asymmetric Digital Signatures',
        detail: 'Automated batch manifest hashing (SHA-256) and RSA digital signing via KMS sign API to guarantee data lake integrity.',
        status: 'ENFORCED',
        badge: 'RSASSA_PKCS1_V1_5',
      },
    ],
  },
  {
    category: 'Storage & Data Lake Hardening',
    items: [
      {
        name: 'TLS 1.2+ Transport Enforcement',
        detail: 'S3 bucket policies strictly deny non-HTTPS traffic (aws:SecureTransport = false) across all buckets.',
        status: 'ENFORCED',
        badge: 'TLS 1.2 / 1.3',
      },
      {
        name: 'S3 Public Access Block',
        detail: 'BlockPublicAcls, BlockPublicPolicy, IgnorePublicAcls, and RestrictPublicBuckets enabled on all 4 buckets.',
        status: 'ENFORCED',
        badge: 'Zero Public S3',
      },
      {
        name: 'Compulsory SSE-KMS at Rest',
        detail: 'DenyNonKmsPutObject policies reject any object upload not explicitly encrypted with the CMK.',
        status: 'ENFORCED',
        badge: 'SSE-KMS',
      },
    ],
  },
  {
    category: 'Data Privacy & AI Safety',
    items: [
      {
        name: 'Automated PII Redaction',
        detail: 'Amazon Comprehend detects and masks names, phone numbers, and student emails with [NAME_REDACTED] before landing in analytics lake.',
        status: 'ENFORCED',
        badge: 'Comprehend PII',
      },
      {
        name: 'Prompt Injection Defense',
        detail: 'System prompt delimiter wrapping, strict ground-truth citation constraint, and max token limits prevent jailbreaks.',
        status: 'ENFORCED',
        badge: 'Bedrock Guardrail',
      },
    ],
  },
  {
    category: 'Identity, RBAC & Governance',
    items: [
      {
        name: 'Cognito JWT Authorizer & Role RBAC',
        detail: 'HTTP API Gateway enforces signed JWT tokens. Fine-grained RBAC restricts pipeline uploads to Admin group only.',
        status: 'ENFORCED',
        badge: 'Cognito + JWT',
      },
      {
        name: 'Least-Privilege IAM Execution Roles',
        detail: 'Dedicated per-Lambda IAM roles with resource-scoped policies; zero wildcard IAM statements on sensitive actions.',
        status: 'ENFORCED',
        badge: 'Least Privilege',
      },
      {
        name: 'CloudTrail Audit Logging & CloudWatch Alarms',
        detail: 'Management events logged to encrypted S3 & CloudWatch Logs with metric filters tracking unauthorized attempts.',
        status: 'ENFORCED',
        badge: 'CloudTrail + SNS',
      },
    ],
  },
]
</script>

<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Security Controls & Compliance Matrix
        </h1>
        <p class="text-sm text-slate-500 dark:text-slate-400">
          Wipro CPPE Module 4 (Cloud Security, Cryptography & Governance) Architecture Evidence
        </p>
      </div>
      <div class="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3.5 py-1.5 text-xs font-semibold text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300">
        <span>🛡️ 100% Security Controls Enforced</span>
      </div>
    </div>

    <!-- Controls Categories Grid -->
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div
        v-for="cat in controls"
        :key="cat.category"
        class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"
      >
        <h3 class="text-base font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
          <span>🔒</span>
          <span>{{ cat.category }}</span>
        </h3>

        <div class="space-y-4">
          <div
            v-for="item in cat.items"
            :key="item.name"
            class="rounded-xl border border-slate-100 bg-slate-50/60 p-4 transition-all hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-850"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-xs text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 font-bold">
                  ✓
                </span>
                <h4 class="text-sm font-semibold text-slate-900 dark:text-white">
                  {{ item.name }}
                </h4>
              </div>
              <span class="rounded bg-indigo-50 px-2 py-0.5 text-[10px] font-mono font-semibold text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300">
                {{ item.badge }}
              </span>
            </div>

            <p class="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              {{ item.detail }}
            </p>

            <div class="mt-3 flex items-center gap-2 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
              <span class="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Status: {{ item.status }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Governance Summary Banner -->
    <div class="rounded-2xl border border-indigo-200 bg-gradient-to-r from-indigo-50 to-violet-50 p-6 dark:border-indigo-900/60 dark:from-indigo-950/40 dark:to-violet-950/30">
      <div class="flex items-start gap-4">
        <div class="text-3xl">📋</div>
        <div>
          <h4 class="text-sm font-bold text-indigo-950 dark:text-indigo-200">
            Auditability & Non-Repudiation Assurance
          </h4>
          <p class="mt-1 text-xs text-indigo-800/80 dark:text-indigo-300/80 leading-relaxed">
            All student feedback records are cryptographically traceable through immutable S3 versioning, KMS manifest digital signatures, and CloudTrail event logs. In compliance with student privacy regulations, unmasked raw records remain isolated in KMS-secured storage with strict least-privilege administrative access.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
