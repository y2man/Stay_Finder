import { useState, useEffect, FormEvent } from 'react'
import { useSearchParams, useNavigate, useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Search, ShieldCheck, Sparkles, Wallet } from 'lucide-react'
import { api, assetUrl, Property } from './api'
import { useStore } from './store'
import { PropertyCard, Reveal, Magnetic, Counter, Skeleton, Tilt } from './ui'

const usePage = (qs: string) =>
  useQuery({
    queryKey: ['p', qs],
    queryFn: () =>
      api<{ total: number; items: Property[] }>(`/properties?${qs}`)
  })

export function HomePage () {
  const nav = useNavigate()
  const feat = usePage('size=6&sort=rating')
  const dest = useQuery({
    queryKey: ['d'],
    queryFn: () => api<any[]>('/destinations')
  })
  const go = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const p = new URLSearchParams()
    new FormData(e.currentTarget).forEach((v, k) => v && p.set(k, String(v)))
    nav('/explore?' + p)
  }
  return (
    <div className='max-w-6xl mx-auto px-4'>
      <section className='pt-20 pb-16 grid lg:grid-cols-2 gap-10 items-center'>
        <div>
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            className='text-5xl md:text-6xl font-extrabold leading-tight'
          >
            Find Your Place. Discover Your World.
          </motion.h1>
          <p className='mt-5 opacity-75 max-w-md'>
            Discover extraordinary stays, explore beautiful destinations, and
            make every journey unforgettable.
          </p>
        </div>
        <div className='relative h-64 hidden lg:block'>
          {(feat.data?.items ?? []).slice(0, 3).map((p, i) => (
            <motion.img
              key={p.id}
              src={assetUrl(p.image_url)}
              alt=''
              className='glass absolute w-56 h-40 object-cover p-1'
              style={{ left: i * 90, top: i * 40 }}
              animate={{
                y: [0, -14, 0],
                rotate: [i * 3 - 3, i * 3, i * 3 - 3]
              }}
              transition={{ duration: 5 + i, repeat: Infinity }}
            />
          ))}
        </div>
      </section>
      <form onSubmit={go} className='glass p-4 grid gap-3 md:grid-cols-6 -mt-4'>
        <input
          name='q'
          placeholder='Where to?'
          aria-label='Destination'
          className='inp md:col-span-2'
        />
        <input
          name='check_in'
          type='date'
          aria-label='Check-in'
          className='inp'
        />
        <input
          name='check_out'
          type='date'
          aria-label='Check-out'
          className='inp'
        />
        <input
          name='guests'
          type='number'
          min={1}
          placeholder='Guests'
          aria-label='Guests'
          className='inp'
        />
        <Magnetic
          type='submit'
          className='flex items-center justify-center gap-2'
        >
          <Search size={18} />
          Search
        </Magnetic>
      </form>
      <Reveal>
        <div className='grid grid-cols-3 text-center my-16 gap-4'>
          {[
            [(dest.data ?? []).length, '', 'Destinations'],
            [feat.data?.total ?? 0, '', 'Stays'],
            [98, '%', 'Happy guests']
          ].map(([n, s, l]: any) => (
            <div key={l} className='glass py-6'>
              <div className='text-4xl font-extrabold text-amber-400'>
                <Counter to={n} suffix={s} />
              </div>
              <div className='opacity-70'>{l}</div>
            </div>
          ))}
        </div>
      </Reveal>
      <Reveal>
        <h2 className='text-2xl font-bold mb-5'>Popular destinations</h2>
      </Reveal>
      <div className='grid sm:grid-cols-3 gap-5'>
        {(dest.data ?? []).map(d => (
          <Reveal key={d.id}>
            <Tilt>
              <Link
                to={`/explore?q=${d.city}`}
                className='glass glow block overflow-hidden group'
              >
                <img
                  src={assetUrl(d.image_url)}
                  alt={d.city}
                  loading='lazy'
                  className='h-40 w-full object-cover group-hover:scale-110 transition duration-700'
                />
                <div className='p-4'>
                  <b>{d.city}</b>, {d.country}
                  <p className='opacity-70 text-sm'>
                    {d.properties} properties
                  </p>
                </div>
              </Link>
            </Tilt>
          </Reveal>
        ))}
      </div>
      <Reveal>
        <h2 className='text-2xl font-bold mt-16 mb-5'>Top-rated stays</h2>
      </Reveal>
      <div className='grid sm:grid-cols-2 lg:grid-cols-3 gap-6'>
        {feat.isLoading
          ? [0, 1, 2].map(i => <Skeleton key={i} />)
          : feat.data?.items.map(p => <PropertyCard key={p.id} p={p} />)}
      </div>
      <Reveal>
        <div className='grid md:grid-cols-3 gap-5 my-16'>
          {[
            [Search, 'Search', 'Filter by place, price and dates.'],
            [ShieldCheck, 'Book safely', 'Dates can never be double-booked.'],
            [Wallet, 'Clear prices', 'Fees are calculated on our server.']
          ].map(([I, t, d]: any) => (
            <motion.div whileHover={{ y: -6 }} key={t} className='glass p-6'>
              <I className='text-sky-400 mb-3' />
              <b>{t}</b>
              <p className='opacity-70 text-sm mt-1'>{d}</p>
            </motion.div>
          ))}
        </div>
      </Reveal>
      <Reveal>
        <div className='glass p-10 text-center mb-20'>
          <Sparkles className='mx-auto text-amber-400 mb-2' />
          <h2 className='text-3xl font-bold'>Own a place? Become a host.</h2>
          <Link to='/auth?mode=register' className='btn inline-block mt-5'>
            Start hosting
          </Link>
        </div>
      </Reveal>
    </div>
  )
}

export function ExplorePage () {
  const [params, setParams] = useSearchParams()
  const [list, setList] = useState(false)
  const set = (k: string, v: string) => {
    const p = new URLSearchParams(params)
    v ? p.set(k, v) : p.delete(k)
    if (k !== 'page') p.delete('page')
    setParams(p)
  }
  const { data, isLoading, isError } = usePage(params.toString())
  const page = +(params.get('page') ?? 1)
  const F = ({ k, ...r }: any) => (
    <input
      className='inp'
      value={params.get(k) ?? ''}
      onChange={e => set(k, e.target.value)}
      {...r}
    />
  )
  return (
    <div className='max-w-6xl mx-auto px-4 py-10 grid lg:grid-cols-[260px_1fr] gap-6'>
      <aside className='glass p-4 space-y-3 h-fit lg:sticky top-24'>
        <b>Filters</b>
        <F k='q' placeholder='City, country or name' aria-label='Search' />
        <div className='grid grid-cols-2 gap-2'>
          <F k='min_price' type='number' placeholder='Min $' />
          <F k='max_price' type='number' placeholder='Max $' />
        </div>
        <select
          className='inp'
          value={params.get('category') ?? ''}
          onChange={e => set('category', e.target.value)}
          aria-label='Category'
        >
          <option value=''>Any type</option>
          <option>apartment</option>
          <option>villa</option>
          <option>house</option>
        </select>
        <F k='bedrooms' type='number' min={1} placeholder='Min bedrooms' />
        <F k='guests' type='number' min={1} placeholder='Guests' />
        <F k='check_in' type='date' aria-label='Check-in' />
        <F k='check_out' type='date' aria-label='Check-out' />
        <button
          className='opacity-70 text-sm underline'
          onClick={() => setParams({})}
        >
          Clear all
        </button>
      </aside>
      <div>
        <div className='flex justify-between mb-4 items-center'>
          <span>{data?.total ?? '…'} stays</span>
          <div className='flex gap-2'>
            <select
              className='inp !w-auto'
              value={params.get('sort') ?? 'popular'}
              onChange={e => set('sort', e.target.value)}
              aria-label='Sort'
            >
              <option value='popular'>Newest</option>
              <option value='price_asc'>Price: low</option>
              <option value='price_desc'>Price: high</option>
              <option value='rating'>Top rated</option>
            </select>
            <button className='glass px-3' onClick={() => setList(!list)}>
              {list ? 'Grid' : 'List'}
            </button>
          </div>
        </div>
        <div
          className={
            list ? 'space-y-5' : 'grid sm:grid-cols-2 xl:grid-cols-3 gap-6'
          }
        >
          {isLoading
            ? [0, 1, 2, 3].map(i => <Skeleton key={i} />)
            : data?.items.map(p => (
                <PropertyCard key={p.id} p={p} list={list} />
              ))}
        </div>
        {isError && (
          <p role='alert' className='glass p-8 text-center'>
            Could not load stays. Make sure the API and database are running,
            then refresh.
          </p>
        )}
        {data?.items.length === 0 && (
          <p className='glass p-8 text-center'>
            No stays match. Try different dates or a wider budget.
          </p>
        )}
        <div className='flex justify-center gap-3 mt-8'>
          <button
            disabled={page < 2}
            className='btn'
            onClick={() => set('page', String(page - 1))}
          >
            Previous
          </button>
          <button
            disabled={!data || page * 12 >= data.total}
            className='btn'
            onClick={() => set('page', String(page + 1))}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}

export function PropertyPage () {
  const { id } = useParams()
  const { token, say } = useStore()
  const nav = useNavigate()
  const [f, setF] = useState({ check_in: '', check_out: '', guests: 1 })
  const p = useQuery({
    queryKey: ['prop', id],
    queryFn: () => api<Property & { cleaning_fee: string }>(`/properties/${id}`)
  })
  const ok = f.check_in && f.check_out && f.check_out > f.check_in
  const q = useQuery({
    queryKey: ['quote', id, f],
    enabled: !!ok,
    retry: false,
    queryFn: () =>
      api<any>('/bookings/quote', {
        method: 'POST',
        body: { property_id: id, ...f }
      })
  })
  const book = useMutation({
    mutationFn: () =>
      api('/bookings', { method: 'POST', body: { property_id: id, ...f } }),
    onSuccess: () => {
      say('Booking requested. Find it under My trips.')
      nav('/trips')
    },
    onError: (e: Error) => say(e.message)
  })
  if (p.isLoading)
    return (
      <div className='max-w-5xl mx-auto p-10'>
        <Skeleton h='h-96' />
      </div>
    )
  if (p.isError || !p.data)
    return (
      <div className='max-w-5xl mx-auto p-10 glass'>
        Could not load this property. It may have been removed or the API is
        unavailable.
      </div>
    )
  const d = p.data
  const row = (a: string, b: string) => (
    <div className='flex justify-between'>
      <span className='opacity-70'>{a}</span>
      <span>${b}</span>
    </div>
  )
  return (
    <div className='max-w-6xl mx-auto px-4 py-10 grid lg:grid-cols-[1fr_360px] gap-8'>
      <div>
        <motion.img
          layoutId={d.id}
          initial={{ scale: 1.05 }}
          animate={{ scale: 1 }}
          src={assetUrl(d.image_url)}
          alt={d.title}
          className='glass w-full h-96 object-cover p-1'
        />
        <h1 className='text-3xl font-bold mt-6'>{d.title}</h1>
        <p className='opacity-70'>
          {d.city}, {d.country} · {d.bedrooms} bedrooms · {d.bathrooms}{' '}
          bathrooms · up to {d.max_guests} guests · {d.min_nights} night minimum
          · ★ {d.rating}
        </p>
        <p className='mt-5'>{d.description}</p>
        <div className='flex gap-2 mt-4 flex-wrap'>
          {d.amenities?.map(a => (
            <span key={a} className='glass px-3 py-1 text-sm'>
              {a}
            </span>
          ))}
        </div>
        {d.latitude && d.longitude && (
          <div className='glass p-4 mt-6'>
            <b>Location</b>
            <p className='text-sm opacity-70'>
              {d.city}, {d.country} · Coordinates: {d.latitude}, {d.longitude}
            </p>
            <iframe
              title={`Map showing ${d.city}`}
              className='w-full h-64 rounded-xl mt-3 border-0'
              loading='lazy'
              src={`https://www.openstreetmap.org/export/embed.html?bbox=${
                Number(d.longitude) - 0.025
              }%2C${Number(d.latitude) - 0.025}%2C${
                Number(d.longitude) + 0.025
              }%2C${Number(d.latitude) + 0.025}&layer=mapnik&marker=${
                d.latitude
              }%2C${d.longitude}`}
            />
            <a
              className='underline text-sky-300'
              target='_blank'
              rel='noreferrer'
              href={`https://www.openstreetmap.org/?mlat=${d.latitude}&mlon=${d.longitude}#map=14/${d.latitude}/${d.longitude}`}
            >
              Open larger map
            </a>
          </div>
        )}
        <PropertyReviews propertyId={d.id} />
      </div>
      <aside className='glass p-5 h-fit lg:sticky top-24 space-y-3'>
        <p className='text-2xl font-bold text-amber-400'>
          ${d.price_per_night}
          <span className='text-sm opacity-60 font-normal'> / night</span>
        </p>
        <input
          className='inp'
          type='date'
          min={new Date().toISOString().slice(0, 10)}
          aria-label='Check-in'
          onChange={e => setF({ ...f, check_in: e.target.value })}
        />
        <input
          className='inp'
          type='date'
          min={f.check_in || new Date().toISOString().slice(0, 10)}
          aria-label='Check-out'
          onChange={e => setF({ ...f, check_out: e.target.value })}
        />
        <input
          className='inp'
          type='number'
          min={1}
          max={d.max_guests}
          value={f.guests}
          aria-label='Guests'
          onChange={e => setF({ ...f, guests: +e.target.value })}
        />
        {q.isError && (
          <p role='alert' className='text-sm text-red-400'>
            {(q.error as Error).message}
          </p>
        )}
        {q.data && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className='text-sm space-y-1'
          >
            {row(`${q.data.nights} nights`, q.data.subtotal)}
            {row('Cleaning', q.data.cleaning_fee)}
            {row('Service fee', q.data.service_fee)}
            {row('Taxes', q.data.taxes)}
            <div className='border-t border-white/20 pt-1 font-bold'>
              {row('Total', q.data.total)}
            </div>
          </motion.div>
        )}
        <Magnetic
          className='w-full'
          disabled={!ok || book.isPending}
          onClick={() => (token ? book.mutate() : nav('/auth'))}
        >
          {book.isPending
            ? 'Reserving…'
            : token
            ? 'Reserve'
            : 'Log in to reserve'}
        </Magnetic>
      </aside>
    </div>
  )
}

export function AuthPage () {
  const [sp, setSp] = useSearchParams()
  const reg = sp.get('mode') === 'register'

  const { login, say } = useStore()
  const nav = useNavigate()

  const m = useMutation({
    mutationFn: (b: any) =>
      api<any>(reg ? '/auth/register' : '/auth/login', {
        method: 'POST',
        body: b
      }),

    onSuccess: async r => {
      login(r.access_token, r.role, r.refresh_token)

      if (reg) {
        try {
          const v = await api<any>('/auth/verify-email/request', {
            method: 'POST'
          })

          if (v.development_token) {
            say(
              'Email service is not configured. Use the development verification link.'
            )
            nav(`/verify-email?token=${v.development_token}`)
            return
          }

          if (v.email_sent) {
            say('Verification email sent. Please check your inbox.')
          }
        } catch {}
      }

      say('Welcome to StayFinder')
      nav('/explore')
    },

    onError: (e: Error) => say(e.message)
  })

  const submit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    m.mutate(Object.fromEntries(new FormData(e.currentTarget)))
  }

  return (
    <motion.form
      onSubmit={submit}
      initial={{ rotateY: 90, opacity: 0 }}
      animate={{ rotateY: 0, opacity: 1 }}
      key={String(reg)}
      className='glass max-w-md mx-auto my-16 p-8 space-y-4'
    >
      <h1 className='text-2xl font-bold'>
        {reg ? 'Create your account' : 'Welcome back'}
      </h1>

      {reg && (
        <>
          <input
            className='inp'
            name='full_name'
            placeholder='Full name'
            required
          />

          <select className='inp' name='role' aria-label='Role'>
            <option value='guest'>I want to book stays</option>
            <option value='host'>I want to host</option>
          </select>
        </>
      )}

      <input
        className='inp'
        name='email'
        type='email'
        placeholder='Email'
        required
      />

      <input
        className='inp'
        name='password'
        type='password'
        minLength={8}
        placeholder='Password (8+ characters)'
        required
      />

      <Magnetic type='submit' className='w-full' disabled={m.isPending}>
        {m.isPending ? 'Please wait…' : reg ? 'Sign up' : 'Log in'}
      </Magnetic>

      <button
        type='button'
        className='text-sm opacity-70 underline'
        onClick={() => setSp(reg ? {} : { mode: 'register' })}
      >
        {reg ? 'Have an account? Log in' : 'New here? Sign up'}
      </button>

      {!reg && (
        <Link
          to='/forgot-password'
          className='block text-sm underline opacity-70'
        >
          Forgot password?
        </Link>
      )}
    </motion.form>
  )
}

export function TripsPage () {
  const qc = useQueryClient(),
    say = useStore(s => s.say)
  const t = useQuery({
    queryKey: ['trips'],
    queryFn: () => api<any[]>('/bookings/me')
  })
  const c = useMutation({
    mutationFn: (id: string) =>
      api(`/bookings/${id}/cancel`, { method: 'POST' }),
    onSuccess: () => {
      say('Booking cancelled')
      qc.invalidateQueries({ queryKey: ['trips'] })
    }
  })
  return (
    <div className='max-w-3xl mx-auto px-4 py-10 space-y-4'>
      <h1 className='text-3xl font-bold'>My trips</h1>
      {t.data?.length === 0 && (
        <p className='glass p-8'>
          No trips yet.{' '}
          <Link to='/explore' className='underline'>
            Find a stay
          </Link>
          .
        </p>
      )}
      {t.data?.map(b => (
        <motion.div
          layout
          key={b.id}
          className='glass p-4 flex justify-between items-center'
        >
          <div>
            <b>{b.property_title || 'Stay'}</b>
            <p>
              {b.check_in} → {b.check_out}
            </p>
            <p className='opacity-70 text-sm'>
              {b.status} · Payment: {b.payment_status || 'unpaid'} · ${b.total}
            </p>
            {b.host_id && (
              <Link
                className='text-sm underline'
                to={`/messages?other_user=${b.host_id}&booking_id=${b.id}`}
              >
                Message host
              </Link>
            )}
            {b.status === 'confirmed' &&
              b.check_out <= new Date().toISOString().slice(0, 10) && (
                <ReviewForm bookingId={b.id} />
              )}
          </div>
          <div className='flex gap-2'>
            {b.status === 'confirmed' && b.payment_status !== 'paid' && (
              <button
                className='btn'
                onClick={async () => {
                  try {
                    const r = await api<any>('/payments/checkout', {
                      method: 'POST',
                      body: { booking_id: b.id }
                    })
                    window.location.href = r.checkout_url
                  } catch (e) {
                    say((e as Error).message)
                  }
                }}
              >
                Pay securely
              </button>
            )}
            {['pending', 'confirmed'].includes(b.status) && (
              <button className='btn' onClick={() => c.mutate(b.id)}>
                Cancel
              </button>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  )
}

function ReviewForm ({ bookingId }: { bookingId: string }) {
  const [rating, setRating] = useState('5')
  const [comment, setComment] = useState('')
  const [done, setDone] = useState(false)
  const say = useStore(s => s.say)
  return (
    <form
      className='mt-3 space-y-2'
      onSubmit={async e => {
        e.preventDefault()
        try {
          await api('/reviews', {
            method: 'POST',
            body: { booking_id: bookingId, rating: Number(rating), comment }
          })
          setDone(true)
          say('Review submitted')
        } catch (err) {
          say((err as Error).message)
        }
      }}
    >
      {done ? (
        <p className='text-sm text-emerald-300'>Thank you for your review.</p>
      ) : (
        <>
          <div className='flex gap-2'>
            <select
              className='inp !w-24'
              value={rating}
              onChange={e => setRating(e.target.value)}
            >
              <option value='5'>5 stars</option>
              <option value='4'>4 stars</option>
              <option value='3'>3 stars</option>
              <option value='2'>2 stars</option>
              <option value='1'>1 star</option>
            </select>
            <input
              className='inp'
              value={comment}
              onChange={e => setComment(e.target.value)}
              placeholder='Share your experience'
              minLength={5}
              required
            />
          </div>
          <button className='btn text-sm'>Leave review</button>
        </>
      )}
    </form>
  )
}

export function PropertyReviews ({ propertyId }: { propertyId: string }) {
  const { data = [], isLoading } = useQuery({
    queryKey: ['reviews', propertyId],
    queryFn: () => api<any[]>(`/properties/${propertyId}/reviews`)
  })
  return (
    <section className='mt-8'>
      <h2 className='text-2xl font-bold mb-3'>Guest reviews</h2>
      {isLoading ? (
        <p>Loading reviews…</p>
      ) : data.length ? (
        <div className='space-y-3'>
          {data.map((r: any) => (
            <article key={r.id} className='glass p-4'>
              <div className='flex justify-between'>
                <b>{r.guest_name}</b>
                <span>★ {r.rating}/5</span>
              </div>
              <p className='mt-2'>{r.comment}</p>
              <small className='opacity-60'>
                {String(r.created_at).slice(0, 10)}
              </small>
            </article>
          ))}
        </div>
      ) : (
        <p className='opacity-70'>
          No reviews yet. Be the first to share your experience after a
          completed stay.
        </p>
      )}
    </section>
  )
}

export function FavoritesPage () {
  const {
    data = [],
    isLoading,
    refetch
  } = useQuery({
    queryKey: ['favorites'],
    queryFn: () => api<Property[]>('/favorites')
  })
  return (
    <div className='max-w-6xl mx-auto px-4 py-10'>
      <h1 className='text-3xl font-bold mb-6'>Saved stays</h1>
      {isLoading ? (
        <Skeleton />
      ) : data.length ? (
        <div className='grid sm:grid-cols-2 lg:grid-cols-3 gap-6'>
          {data.map(p => (
            <div key={p.id}>
              <PropertyCard p={p} />
              <button
                className='mt-2 underline text-sm'
                onClick={async () => {
                  await api(`/favorites/${p.id}`, { method: 'DELETE' })
                  refetch()
                }}
              >
                Remove from saved
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className='glass p-8'>You haven't saved any stays yet.</p>
      )}
    </div>
  )
}

export function HostPage () {
  const qc = useQueryClient(),
    say = useStore(s => s.say)
  const props = useQuery({
    queryKey: ['host-properties'],
    queryFn: () => api<any[]>('/host/properties')
  })
  const bookings = useQuery({
    queryKey: ['host-bookings'],
    queryFn: () => api<any[]>('/host/bookings')
  })
  const [editing, setEditing] = useState<any>(null)
  const [form, setForm] = useState<any>({
    title: '',
    description: '',
    city: 'Addis Ababa',
    country: 'Ethiopia',
    category: 'apartment',
    price_per_night: 60,
    cleaning_fee: 0,
    bedrooms: 1,
    bathrooms: 1,
    max_guests: 2,
    min_nights: 1,
    image_url: '',
    amenities: 'WiFi, Kitchen',
    latitude: '',
    longitude: '',
    published: true
  })
  const save = useMutation({
    mutationFn: () =>
      api(editing ? `/host/properties/${editing}` : '/host/properties', {
        method: editing ? 'PUT' : 'POST',
        body: {
          ...form,
          amenities: form.amenities
            .split(',')
            .map((x: string) => x.trim())
            .filter(Boolean),
          latitude: form.latitude === '' ? null : Number(form.latitude),
          longitude: form.longitude === '' ? null : Number(form.longitude)
        }
      }),
    onSuccess: () => {
      say('Listing saved')
      setEditing(null)
      setForm({ ...form, title: '', description: '' })
      qc.invalidateQueries({ queryKey: ['host-properties'] })
    },
    onError: e => say((e as Error).message)
  })
  const decide = async (id: string, approve: boolean) => {
    try {
      await api(`/host/bookings/${id}/decision?approve=${approve}`, {
        method: 'POST'
      })
      say('Booking updated')
      qc.invalidateQueries({ queryKey: ['host-bookings'] })
    } catch (e) {
      say((e as Error).message)
    }
  }
  const field = (key: string, label: string, type = 'text') => (
    <label className='block text-sm'>
      {label}
      <input
        className='inp mt-1'
        type={type}
        value={form[key]}
        onChange={e => setForm({ ...form, [key]: e.target.value })}
        required={!['latitude', 'longitude'].includes(key)}
      />
    </label>
  )
  return (
    <div className='max-w-6xl mx-auto px-4 py-10 space-y-8'>
      <div>
        <h1 className='text-3xl font-bold'>Host dashboard</h1>
        <p className='opacity-70'>
          Manage your listings and reservation requests.
        </p>
      </div>
      <section className='glass p-5'>
        <h2 className='text-xl font-bold mb-4'>
          {editing ? 'Edit listing' : 'Create a listing'}
        </h2>
        <div className='grid sm:grid-cols-2 lg:grid-cols-3 gap-3'>
          {field('title', 'Property title')}
          {field('city', 'City')}
          {field('country', 'Country')}
          {field('price_per_night', 'Price per night (USD)', 'number')}
          {field('cleaning_fee', 'Cleaning fee (USD)', 'number')}
          {field('bedrooms', 'Bedrooms', 'number')}
          {field('bathrooms', 'Bathrooms', 'number')}
          {field('max_guests', 'Maximum guests', 'number')}
          {field('min_nights', 'Minimum nights', 'number')}
          {field('latitude', 'Latitude', 'number')}
          {field('longitude', 'Longitude', 'number')}
          {field('image_url', 'Image URL')}
        </div>
        <label className='block mt-3 text-sm'>
          Description
          <textarea
            className='inp mt-1'
            rows={3}
            value={form.description}
            onChange={e => setForm({ ...form, description: e.target.value })}
          />
        </label>
        <label className='block mt-3 text-sm'>
          Amenities (comma separated)
          <input
            className='inp mt-1'
            value={form.amenities}
            onChange={e => setForm({ ...form, amenities: e.target.value })}
          />
        </label>
        <label className='block mt-3 text-sm'>
          Upload a property image (JPG, PNG or WebP, max 8 MB)
          <input
            className='inp mt-1'
            type='file'
            accept='image/png,image/jpeg,image/webp'
            onChange={async e => {
              const file = e.target.files?.[0]
              if (!file) return
              const data = new FormData()
              data.append('file', file)
              try {
                const result = await api<{ url: string }>('/uploads/image', {
                  method: 'POST',
                  body: data
                })
                setForm((f: any) => ({ ...f, image_url: result.url }))
                say('Image uploaded')
              } catch (err) {
                say((err as Error).message)
              }
            }}
          />
        </label>
        <div className='flex gap-3 mt-4'>
          <button
            className='btn'
            disabled={save.isPending}
            onClick={() => save.mutate()}
          >
            {save.isPending ? 'Saving…' : 'Save listing'}
          </button>
          {editing && (
            <button
              className='glass px-4'
              onClick={() => {
                setEditing(null)
              }}
            >
              Cancel edit
            </button>
          )}
        </div>
      </section>
      <section>
        <h2 className='text-xl font-bold mb-3'>Your listings</h2>
        {props.data?.map(p => (
          <div
            key={p.id}
            className='glass p-4 mb-3 flex flex-wrap justify-between gap-3'
          >
            <div>
              <b>{p.title}</b>
              <p className='text-sm opacity-70'>
                {p.city}, {p.country} · ${p.price_per_night}/night ·{' '}
                {p.published ? 'Published' : 'Unpublished'}
              </p>
            </div>
            <div className='flex gap-2'>
              <button
                className='btn'
                onClick={() => {
                  setEditing(p.id)
                  setForm({
                    ...p,
                    amenities: (p.amenities || []).join(', '),
                    latitude: p.latitude ?? '',
                    longitude: p.longitude ?? ''
                  })
                  window.scrollTo({ top: 0, behavior: 'smooth' })
                }}
              >
                Edit
              </button>
              <button
                className='glass px-3'
                onClick={async () => {
                  if (confirm('Delete or unpublish this listing?')) {
                    await api(`/host/properties/${p.id}`, { method: 'DELETE' })
                    qc.invalidateQueries({ queryKey: ['host-properties'] })
                  }
                }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </section>
      <section>
        <h2 className='text-xl font-bold mb-3'>Reservation requests</h2>
        {bookings.data?.map(b => (
          <div key={b.id} className='glass p-4 mb-3'>
            <b>{b.property_title}</b>
            <p className='text-sm opacity-70'>
              {b.guest_name} · {b.check_in} → {b.check_out} · {b.guests} guests
              · ${b.total} · {b.status}
            </p>
            <Link
              className='text-sm underline'
              to={`/messages?other_user=${b.guest_id}&booking_id=${b.id}`}
            >
              Message guest
            </Link>
            {b.status === 'pending' && (
              <div className='flex gap-2 mt-2'>
                <button className='btn' onClick={() => decide(b.id, true)}>
                  Approve
                </button>
                <button
                  className='glass px-3'
                  onClick={() => decide(b.id, false)}
                >
                  Decline
                </button>
              </div>
            )}
          </div>
        ))}
      </section>
    </div>
  )
}

export function AssistantPage () {
  const [message, setMessage] = useState('')
  const [history, setHistory] = useState<{ role: string; content: string }[]>([
    {
      role: 'assistant',
      content:
        "Hi! Tell me where you'd like to go, your budget, dates, and what matters most in a stay. I can help you plan your search."
    }
  ])
  const [busy, setBusy] = useState(false)
  const say = useStore(s => s.say)
  const send = async (e: FormEvent) => {
    e.preventDefault()
    if (!message.trim() || busy) return
    const text = message.trim()
    setMessage('')
    setHistory(h => [...h, { role: 'user', content: text }])
    setBusy(true)
    try {
      const r = await api<{ reply: string }>('/assistant', {
        method: 'POST',
        body: { message: text }
      })
      setHistory(h => [...h, { role: 'assistant', content: r.reply }])
    } catch (err) {
      say((err as Error).message)
      setHistory(h => [
        ...h,
        {
          role: 'assistant',
          content:
            "I couldn't reach the assistant service. Please check the AI configuration and try again."
        }
      ])
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className='max-w-3xl mx-auto px-4 py-10'>
      <h1 className='text-3xl font-bold'>StayFinder AI travel assistant</h1>
      <p className='opacity-70 mb-5'>
        Get help comparing stays and planning your search.
      </p>
      <div className='glass p-4 min-h-96 space-y-3'>
        {history.map((m, i) => (
          <div
            key={i}
            className={`p-3 rounded-xl max-w-[90%] ${
              m.role === 'user' ? 'ml-auto bg-violet-600/30' : 'bg-white/10'
            }`}
          >
            <b className='text-xs uppercase opacity-60'>{m.role}</b>
            <p className='whitespace-pre-wrap mt-1'>{m.content}</p>
          </div>
        ))}
        {busy && <p className='opacity-60'>Thinking…</p>}
      </div>
      <form className='flex gap-2 mt-3' onSubmit={send}>
        <input
          className='inp'
          value={message}
          onChange={e => setMessage(e.target.value)}
          placeholder='Ask about destinations, budgets, amenities…'
        />
        <button className='btn' disabled={busy}>
          Send
        </button>
      </form>
    </div>
  )
}

export function MessagesPage () {
  const [sp] = useSearchParams()
  const [other, setOther] = useState(sp.get('other_user') || '')
  const bookingId = sp.get('booking_id')
  const [body, setBody] = useState('')
  const [reload, setReload] = useState(0)
  const say = useStore(s => s.say)
  const q = useQuery({
    queryKey: ['messages', other, reload],
    enabled: !!other,
    queryFn: () => api<any[]>(`/messages?other_user=${other}`),
    refetchInterval: 5000
  })
  const send = async (e: FormEvent) => {
    e.preventDefault()
    try {
      await api('/messages', {
        method: 'POST',
        body: { recipient_id: other, body, booking_id: bookingId }
      })
      setBody('')
      setReload(x => x + 1)
    } catch (e) {
      say((e as Error).message)
    }
  }
  return (
    <div className='max-w-3xl mx-auto px-4 py-10'>
      <h1 className='text-3xl font-bold'>Messages</h1>
      <p className='opacity-70 mb-4'>
        Open a conversation from a booking in My trips or your Host dashboard.
        Messaging is limited to the guest and host on that booking.
      </p>
      <input
        className='inp mb-3'
        value={other}
        onChange={e => setOther(e.target.value)}
        placeholder='Recipient user ID (UUID)'
        readOnly={!other}
      />
      <p className='text-xs opacity-60 mb-3'>
        Booking ID: {bookingId || 'Open this conversation from a booking'}
      </p>
      <div className='glass p-4 min-h-72 space-y-3'>
        {q.data?.map(m => (
          <div key={m.id} className='bg-white/10 rounded-lg p-3'>
            <p>{m.body}</p>
            <small className='opacity-60'>
              {String(m.created_at).replace('T', ' ').slice(0, 16)}
            </small>
          </div>
        ))}
      </div>
      <form className='flex gap-2 mt-3' onSubmit={send}>
        <input
          className='inp'
          value={body}
          onChange={e => setBody(e.target.value)}
          placeholder='Write a message…'
          required
        />
        <button className='btn' disabled={!other}>
          Send
        </button>
      </form>
    </div>
  )
}

export function AdminPage () {
  const overview = useQuery({
    queryKey: ['admin-overview'],
    queryFn: () => api<any>('/admin/overview')
  })
  const users = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => api<any[]>('/admin/users')
  })
  const say = useStore(s => s.say)
  return (
    <div className='max-w-6xl mx-auto px-4 py-10'>
      <h1 className='text-3xl font-bold mb-5'>Admin console</h1>
      <div className='grid sm:grid-cols-4 gap-3'>
        {Object.entries(overview.data || {}).map(([k, v]) => (
          <div className='glass p-5' key={k}>
            <p className='opacity-60 capitalize'>{k}</p>
            <b className='text-2xl'>{String(v)}</b>
          </div>
        ))}
      </div>
      <h2 className='text-xl font-bold mt-8 mb-3'>Users</h2>
      {users.data?.map(u => (
        <div
          className='glass p-3 mb-2 flex justify-between items-center'
          key={u.id}
        >
          <div>
            <b>{u.name}</b>
            <p className='text-sm opacity-70'>
              {u.email} · {u.role}
            </p>
          </div>
          <select
            className='inp !w-auto'
            value={u.role}
            onChange={async e => {
              try {
                await api(`/admin/users/${u.id}/role`, {
                  method: 'PATCH',
                  body: { role: e.target.value }
                })
                users.refetch()
              } catch (err) {
                say((err as Error).message)
              }
            }}
          >
            <option>guest</option>
            <option>host</option>
            <option>admin</option>
          </select>
        </div>
      ))}
      <AdminProperties />
    </div>
  )
}

function AdminProperties () {
  const q = useQuery({
    queryKey: ['admin-properties'],
    queryFn: () => api<any[]>('/admin/properties')
  })
  const qc = useQueryClient()
  const say = useStore(s => s.say)
  return (
    <section className='mt-8'>
      <h2 className='text-xl font-bold mb-3'>Property moderation</h2>
      {q.data?.map(p => (
        <div
          className='glass p-3 mb-2 flex justify-between items-center'
          key={p.id}
        >
          <div>
            <b>{p.title}</b>
            <p className='text-sm opacity-70'>
              {p.city}, {p.country}
            </p>
          </div>
          <button
            className='btn'
            onClick={async () => {
              try {
                await api(
                  `/admin/properties/${p.id}/publish?published=${!p.published}`,
                  { method: 'PATCH' }
                )
                qc.invalidateQueries({ queryKey: ['admin-properties'] })
              } catch (e) {
                say((e as Error).message)
              }
            }}
          >
            {p.published ? 'Unpublish' : 'Publish'}
          </button>
        </div>
      ))}
    </section>
  )
}

export function NotificationsPage () {
  const q = useQuery({
    queryKey: ['notifications'],
    queryFn: () => api<any[]>('/notifications')
  })
  const qc = useQueryClient()
  return (
    <div className='max-w-3xl mx-auto px-4 py-10'>
      <h1 className='text-3xl font-bold mb-5'>Notifications</h1>
      {q.data?.map(n => (
        <button
          key={n.id}
          className={`glass block text-left p-4 w-full mb-3 ${
            n.read ? 'opacity-60' : ''
          }`}
          onClick={async () => {
            await api(`/notifications/${n.id}/read`, { method: 'POST' })
            qc.invalidateQueries({ queryKey: ['notifications'] })
          }}
        >
          <b>{n.title}</b>
          <p>{n.body}</p>
          <small className='opacity-60'>
            {String(n.created_at).slice(0, 16)} ·{' '}
            {n.read ? 'Read' : 'Unread — click to mark read'}
          </small>
        </button>
      ))}
    </div>
  )
}
export function PaymentSuccessPage () {
  return (
    <div className='max-w-xl mx-auto my-20 glass p-8 text-center'>
      <h1 className='text-3xl font-bold'>Payment submitted</h1>
      <p className='mt-3 opacity-70'>
        Your payment provider is sending confirmation. Your booking will show as
        confirmed once the verified payment webhook is received.
      </p>
      <Link className='btn inline-block mt-5' to='/trips'>
        View my trips
      </Link>
    </div>
  )
}

export function ForgotPasswordPage () {
  const [sp] = useSearchParams()
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [token, setToken] = useState(sp.get('token') || '')
  const [password, setPassword] = useState('')
  const [resetMode, setResetMode] = useState(!!sp.get('token'))
  const say = useStore(s => s.say)
  const request = async (e: FormEvent) => {
    e.preventDefault()
    try {
      const r = await api<any>('/auth/password/forgot', {
        method: 'POST',
        body: { email }
      })
      setMessage(r.message)
      if (r.development_token) {
        setToken(r.development_token)
        setResetMode(true)
      }
    } catch (err) {
      say((err as Error).message)
    }
  }
  const reset = async (e: FormEvent) => {
    e.preventDefault()
    try {
      const r = await api<any>('/auth/password/reset', {
        method: 'POST',
        body: { token, password }
      })
      setMessage(r.message)
      setResetMode(false)
    } catch (err) {
      say((err as Error).message)
    }
  }
  return (
    <div className='max-w-md mx-auto my-16 glass p-8'>
      <h1 className='text-2xl font-bold'>Reset your password</h1>
      {message && <p className='my-3'>{message}</p>}
      {!resetMode ? (
        <form className='space-y-3 mt-4' onSubmit={request}>
          <input
            className='inp'
            type='email'
            required
            placeholder='Account email'
            value={email}
            onChange={e => setEmail(e.target.value)}
          />
          <button className='btn w-full'>Request reset link</button>
        </form>
      ) : (
        <form className='space-y-3 mt-4' onSubmit={reset}>
          <label className='block text-sm'>
            Reset token
            <input
              className='inp mt-1'
              value={token}
              onChange={e => setToken(e.target.value)}
              required
            />
          </label>
          <input
            className='inp'
            type='password'
            minLength={8}
            placeholder='New password'
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
          <button className='btn w-full'>Change password</button>
        </form>
      )}
    </div>
  )
}

export function VerifyEmailPage () {
  const [sp] = useSearchParams()
  const [message, setMessage] = useState('Verifying your email…')
  useEffect(() => {
    const token = sp.get('token')
    if (!token) {
      setMessage('Verification token is missing.')
      return
    }
    api('/auth/verify-email', { method: 'POST', body: { token } })
      .then(() =>
        setMessage(
          'Your email is verified. You can now continue using StayFinder.'
        )
      )
      .catch(e => setMessage((e as Error).message))
  }, [])
  return (
    <div className='max-w-xl mx-auto my-20 glass p-8 text-center'>
      <h1 className='text-2xl font-bold'>Email verification</h1>
      <p className='mt-3'>{message}</p>
    </div>
  )
}
