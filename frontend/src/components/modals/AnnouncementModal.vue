<script setup lang="ts">
import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { getAnnouncements, createAnnouncement, updateAnnouncement, deleteAnnouncement } from '../../api/misc'

defineProps<{ show: boolean }>()
const emit = defineEmits(['update:show', 'saved'])
const msg = useMessage()

const list = ref<any[]>([])
const showForm = ref(false)
const editItem = ref<any>(null)
const form = ref({ title: '', content: '', is_pinned: false })
const saving = ref(false)

async function loadData() {
  const { data } = await getAnnouncements()
  list.value = data
}

function openAdd() {
  editItem.value = null
  form.value = { title: '', content: '', is_pinned: false }
  showForm.value = true
}

function openEdit(item: any) {
  editItem.value = item
  form.value = { title: item.title, content: item.content, is_pinned: item.is_pinned }
  showForm.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editItem.value) await updateAnnouncement(editItem.value.id, form.value)
    else await createAnnouncement(form.value)
    showForm.value = false
    await loadData()
    emit('saved')
  } catch { msg.error('保存失败') }
  finally { saving.value = false }
}

async function handleDelete(id: number) {
  await deleteAnnouncement(id)
  await loadData()
  emit('saved')
}
</script>

<template>
  <n-modal :show="show" @update:show="emit('update:show', $event)" preset="card"
    title="公告管理" style="width: 560px" :bordered="false" @after-enter="loadData">
    <template v-if="!showForm">
      <n-button type="primary" size="small" @click="openAdd" style="margin-bottom:12px">新建公告</n-button>
      <div v-for="a in list" :key="a.id" style="padding:8px;border-bottom:1px solid #f0f0f0;display:flex;align-items:center;gap:8px">
        <span style="flex:1;font-weight:500">{{ a.title }}</span>
        <n-tag v-if="a.is_pinned" type="warning" size="tiny">置顶</n-tag>
        <n-button text size="tiny" @click="openEdit(a)">编辑</n-button>
        <n-popconfirm @positive-click="handleDelete(a.id)">
          <template #trigger><n-button text size="tiny" type="error">删除</n-button></template>
          确定删除？
        </n-popconfirm>
      </div>
    </template>
    <template v-else>
      <n-form label-placement="left" label-width="60">
        <n-form-item label="标题"><n-input v-model:value="form.title" /></n-form-item>
        <n-form-item label="内容"><n-input v-model:value="form.content" type="textarea" :rows="4" /></n-form-item>
        <n-form-item label="置顶"><n-switch v-model:value="form.is_pinned" /></n-form-item>
      </n-form>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <n-button @click="showForm = false">返回</n-button>
        <n-button type="primary" :loading="saving" @click="handleSave">保存</n-button>
      </div>
    </template>
  </n-modal>
</template>
