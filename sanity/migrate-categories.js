/**
 * ترحيل التصنيفات القديمة إلى الجديدة — مرة واحدة:
 *   npx sanity exec migrate-categories.js --with-user-token
 * تأمّل → خاطرة · رأي/تجربة → تدوينة
 */
import {getCliClient} from 'sanity/cli'

const client = getCliClient({apiVersion: '2024-01-01'})
const MAP = {'تأمّل': 'خاطرة', 'رأي': 'تدوينة', 'تجربة': 'تدوينة'}

async function main() {
  const posts = await client.fetch('*[_type == "post"]{_id, title, category}')
  for (const p of posts) {
    const next = MAP[p.category]
    if (!next) { console.log(`— ${p.title}: ${p.category} (بلا تغيير)`); continue }
    await client.patch(p._id).set({category: next}).commit()
    console.log(`✓ ${p.title}: ${p.category} → ${next}`)
  }
}
main().catch((e) => { console.error(e); process.exit(1) })
