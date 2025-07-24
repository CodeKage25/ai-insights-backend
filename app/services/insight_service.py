import time
import logging
import asyncio
from typing import List

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from app.models.insight import Insight
from app.core.database import FileRecord, SessionLocal
from app.utils.file_parser import parse_file
from app.core.config import get_settings
from app.core.websocket_manager import manager

logger = logging.getLogger(__name__)
settings = get_settings()


class InsightService:
    @staticmethod
    async def generate_insights_with_progress(file_id: str) -> List[Insight]:
        """
        Generate AI-like insights with real-time progress updates.
        Re-loads FileRecord in its own session to avoid DetachedInstanceError.
        """
        start_time = time.time()
        db: Session = SessionLocal()

        # re-load the FileRecord
        file_record = db.get(FileRecord, file_id)
        if not file_record:
            logger.error(f"InsightService: no FileRecord for {file_id}; aborting")
            await manager.send_status_update(
                file_id,
                "failed",
                "File not found; aborting insights",
                progress=0.0
            )
            db.close()
            return []

        try:
            # notify start
            await manager.send_status_update(
                file_id,
                "processing",
                "Starting analysis...",
                progress=0.0
            )

            #Parse file
            await manager.send_insight_progress(
                file_id,
                "Parsing dataset",
                total_steps=6,
                current_step_num=1
            )
            _, df = parse_file(file_record.filepath)
            await asyncio.sleep(0.5)

            #Validate structure
            await manager.send_insight_progress(
                file_id,
                "Validating data structure",
                total_steps=6,
                current_step_num=2
            )
            await asyncio.sleep(0.3)

            insights: List[Insight] = []

            #Overview
            await manager.send_insight_progress(
                file_id,
                "Analyzing dataset overview",
                total_steps=6,
                current_step_num=3
            )
            overview = await InsightService._generate_overview_insights_async(df)
            insights.extend(overview)
            await manager.send_insight_progress(
                file_id,
                "Analyzing dataset overview",
                total_steps=6,
                current_step_num=3,
                insights_found=len(insights)
            )

            # Statistical
            await manager.send_insight_progress(
                file_id,
                "Performing statistical analysis",
                total_steps=6,
                current_step_num=4,
                insights_found=len(insights)
            )
            stat_ins = await InsightService._generate_statistical_insights_async(df)
            insights.extend(stat_ins)

            # Patterns
            await manager.send_insight_progress(
                file_id,
                "Detecting patterns and correlations",
                total_steps=6,
                current_step_num=5,
                insights_found=len(insights)
            )
            pat_ins = await InsightService._generate_pattern_insights_async(df)
            insights.extend(pat_ins)

            # Quality
            await manager.send_insight_progress(
                file_id,
                "Evaluating data quality",
                total_steps=6,
                current_step_num=6,
                insights_found=len(insights)
            )
            qual_ins = await InsightService._generate_quality_insights_async(df)
            insights.extend(qual_ins)

            # Filter, sort, and trim
            filtered = [i for i in insights if i.confidence >= settings.min_confidence_score]
            filtered.sort(key=lambda x: x.confidence, reverse=True)
            final_insights = filtered[: settings.max_insights]

            # Persist results
            file_record.insights = [ins.dict() for ins in final_insights]
            file_record.processing_status = "completed"
            db.commit()

            processing_time = time.time() - start_time
            await manager.send_insights_complete(
                file_id,
                len(final_insights),
                processing_time
            )

            logger.info(f"Generated {len(final_insights)} insights in {processing_time:.2f}s for file {file_id}")
            return final_insights

        except Exception as e:
            # mark failure
            try:
                file_record.processing_status = "failed"
                db.commit()
            except:
                pass

            await manager.send_status_update(
                file_id,
                "failed",
                f"Analysis failed: {e}",
                progress=0.0
            )
            logger.error(f"Insight generation failed for {file_id}: {e}")
            return []

        finally:
            db.close()


    @staticmethod
    async def _generate_overview_insights_async(df: pd.DataFrame) -> List[Insight]:
        await asyncio.sleep(0.2)
        return InsightService._generate_overview_insights(df)

    @staticmethod
    async def _generate_statistical_insights_async(df: pd.DataFrame) -> List[Insight]:
        await asyncio.sleep(0.8)
        return InsightService._generate_statistical_insights(df)

    @staticmethod
    async def _generate_pattern_insights_async(df: pd.DataFrame) -> List[Insight]:
        await asyncio.sleep(0.6)
        return InsightService._generate_pattern_insights(df)

    @staticmethod
    async def _generate_quality_insights_async(df: pd.DataFrame) -> List[Insight]:
        await asyncio.sleep(0.4)
        return InsightService._generate_quality_insights(df)

    # synchronous insight generators 
    @staticmethod
    def _generate_overview_insights(df: pd.DataFrame) -> List[Insight]:
        return [
            Insight(
                title="Dataset Overview",
                description=(
                    f"Dataset contains {len(df)} rows and {len(df.columns)} columns. "
                    f"Column types: {df.dtypes.value_counts().to_dict()}"
                ),
                confidence=0.95,
                category="overview",
                affected_columns=list(df.columns)
            )
        ]

    @staticmethod
    def _generate_statistical_insights(df: pd.DataFrame) -> List[Insight]:
        insights: List[Insight] = []
        numeric = df.select_dtypes(include=[np.number]).columns
        for col in numeric:
            series = df[col].dropna()
            if series.empty:
                continue

            mean, std = series.mean(), series.std()
            if std > mean * 0.5:
                insights.append(
                    Insight(
                        title=f"High Variability in {col}",
                        description=(
                            f"Column '{col}' CV: {(std/mean)*100:.1f}%. "
                            f"Mean: {mean:.2f}, Std: {std:.2f}"
                        ),
                        confidence=0.8,
                        category="statistical",
                        affected_columns=[col]
                    )
                )

            q1, q3 = series.quantile([0.25, 0.75])
            iqr = q3 - q1
            outliers = series[(series < q1 - 1.5*iqr) | (series > q3 + 1.5*iqr)]
            if not outliers.empty:
                insights.append(
                    Insight(
                        title=f"Outliers Detected in {col}",
                        description=(
                            f"Found {len(outliers)} potential outliers in '{col}'. "
                            f"Range {outliers.min():.2f}–{outliers.max():.2f}"
                        ),
                        confidence=0.75,
                        category="anomaly",
                        affected_columns=[col],
                        affected_rows=outliers.index.tolist()[:10]
                    )
                )
        return insights

    @staticmethod
    def _generate_pattern_insights(df: pd.DataFrame) -> List[Insight]:
        insights: List[Insight] = []
        numeric = df.select_dtypes(include=[np.number]).columns
        if len(numeric) > 1:
            corr = df[numeric].corr()
            for i, c1 in enumerate(numeric):
                for j, c2 in enumerate(numeric[i+1:], start=i+1):
                    val = corr.iat[i, j]
                    if abs(val) > 0.7:
                        rel = "positive" if val > 0 else "negative"
                        insights.append(
                            Insight(
                                title=f"Strong {rel.title()} Correlation",
                                description=(
                                    f"{rel.title()} correlation ({val:.2f}) between '{c1}' and '{c2}'"
                                ),
                                confidence=min(0.9, abs(val)),
                                category="pattern",
                                affected_columns=[c1, c2]
                            )
                        )
        return insights

    @staticmethod
    def _generate_quality_insights(df: pd.DataFrame) -> List[Insight]:
        insights: List[Insight] = []
        total = len(df)
        missing = df.isnull().sum()
        for col, cnt in missing.items():
            pct = (cnt / total) * 100
            if cnt > 0 and pct > 10:
                insights.append(
                    Insight(
                        title=f"Missing Data in {col}",
                        description=(
                            f"Column '{col}' has {cnt} missing values ({pct:.1f}% of total)"
                        ),
                        confidence=0.9,
                        category="data_quality",
                        affected_columns=[col]
                    )
                )
        dupes = df.duplicated().sum()
        if dupes > 0:
            pct = (dupes / total) * 100
            insights.append(
                Insight(
                    title="Duplicate Rows Detected",
                    description=(
                        f"Found {dupes} duplicate rows ({pct:.1f}% of total)"
                    ),
                    confidence=0.95,
                    category="data_quality",
                    affected_columns=list(df.columns)
                )
            )
        return insights
