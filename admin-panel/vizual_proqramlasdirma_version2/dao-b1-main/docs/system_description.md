# Sistem Təsviri — Quadratic Funding DAO (SDF uyğun)

## 1. Ümumi baxış
Bu layihə Quadratic Funding DAO üçün SDF sprint-1 tələblərinə uyğun minimal və istifadəsi rahat ön tərəfi dəstəkləyir. Məqsəd: ictimai xeyirli layihələri cəmiyyət dəstəyi əsasında maliyyələşdirmək və QF alqoritmi ilə həlledici olaraq uyğunluq (matching) məbləğini hesablamaq.

## 2. Aktorlar və əsas proseslər
### Aktorlar
- **Donor (ianəçi)**: Layihələrə vəsait göndərən istifadəçi (wallet ünvanı ilə identifikasiya edilir).
- **Proposer (təklifçi)**: Layihə/tezisi təqdim edən şəxs.
- **Admin**: Roundları konfiqurasiya edən və idarə edən şəxs (məsələn, round açma/bağlama, matching pool təyini).
- **Smart Contract**: On-chain məntiqi yerinə yetirən müqavilələr (donasiya və paylama axını, round nəticələri).

### Əsas proseslər
1. **Proposal Submission**: Təklifçi layihə detallarını və Knowledge Tag-ları daxil edir.
2. **Round Management**: Admin round parametrlərini (başlanğıc/son, matching pool) təyin edir.
3. **Donation & Matching**: Donorlar ianə edirlər; sistem QF formulu əsasında uyğunlaşdırma miqdarını hesablayır.
4. **Finalization**: Round bitdikdə nəticələr bağlanır və məbləğlər təklifçilərə paylanır.

## 3. Əsas entitilər
- **User**: Wallet ünvanı ilə identifikasiya.
- **Proposal**: Layihənin başlığı, təsviri, meta (tags, təklifçi, status).
- **Round**: Vaxt həddi, matching pool və status sahələri ilə.
- **Donation**: Hər donorun layihəyə göndərdiyi qeydlər.
- **MatchingPool**: Round üçün ayrılmış uyğunlaşdırma vəsaiti.

## 4. Müddəalar və məhdudiyyətlər
- **Authentication**: Web3 wallet əsaslı (MetaMask və ya uyğun browser provider).
- **Currency**: ETH və ya seçilmiş ERC20 Governance Token ilə ianələr aparıla bilər.
- **Scalability**: Sürətli axtarış və SEO üçün off-chain indexer (backend) istifadə olunur.
- **Security**: Smart kontraktların auditi tələb olunur; backend server validasiya və rate-limit tətbiq edir.

## 5. SDF uyarlamaları
Bu sənəd SDF tələb və şablonlarına uyğunlaşdırılmışdır: səhifə kontenti SDF işlərini əks etdirir, tələb olunan UML/ERD tərtibatı, export (PNG/PDF) və ZIP submit axını üçün dəstək qeydə alınmışdır.

---
Qeyd: Bu sənəd ön tərəf (frontend) üçün nəzərdə tutulmuş ümumi sistem təsviridir. Backend və smart contract spesifikasiyaları ayrıca sənədlərdə verilməlidir.
